import logging
import time
import re
from typing import List, Tuple
from urllib.parse import urljoin, urlparse

from akamai.edgegrid import EdgeGridAuth

from etwpipeline.contrib.http_utils import resilient_session_factory
from etwpipeline.akamai.model import EdgeHost, Origin, PropertyDescription

logger = logging.getLogger(__name__)

ORIGIN_BEHAVIOR_NAME = "origin"
EDGE_REDIRECTOR_BEHAVIOR_NAME = 'edgeRedirector'
IVM_IMAGES_BEHAVIOR_NAME = 'imageManager'
IVM_VIDEO_BEHAVIOR_NAME = 'imageManagerVideo'
SITESHIELD_BEHAVIOR_NAME = 'siteShield'

def keep_first(iterable, key=None):
    if key is None:
        key = lambda x: x

    seen = set()
    for elem in iterable:
        k = key(elem)
        if k in seen:
            continue

        yield elem
        seen.add(k)

def search_akamai_rule_tree_for_origins(rule_tree) -> List[Origin]:
    behaviors = rule_tree["behaviors"]
    children = rule_tree["children"]
    origins = [
        origin
        for child_rule_tree in children
        for origin in search_akamai_rule_tree_for_origins(child_rule_tree)
    ]
    for behavior in behaviors:
        if behavior.get("name") == ORIGIN_BEHAVIOR_NAME:
            origin_options = behavior["options"]
            hostname = origin_options.get("hostname")
            if hostname is not None:
                origins.append(Origin(name=hostname))

    # TODO: Maybe find a less terrible way to get unique list of origins - check as you go?
    return list(set(origins))

def search_akamai_rule_tree_for_edge_redirector(rule_tree):
    policies = []
    for child in rule_tree['children']:
        policies.append(search_akamai_rule_tree_for_edge_redirector(child))
    for behavior in rule_tree['behaviors']:
        if behavior.get("name") == EDGE_REDIRECTOR_BEHAVIOR_NAME:
            if behavior['options'].get('isSharedPolicy'):
                policy_id = behavior['options']['cloudletSharedPolicy']
            else:
                policy_id = behavior['options']['cloudletPolicy']['id']
            policies.append(str(policy_id))

    # TODO: Maybe find a less terrible way to get unique list of origins - check as you go?
    return list(set(policies))

def search_akamai_rule_tree_for_siteshield(rule_tree):
    siteshield_map = None
    for child in rule_tree['children']:
        siteshield_map = search_akamai_rule_tree_for_edge_redirector(child)
        if siteshield_map is not None:
            break
    for behavior in rule_tree['behaviors']:
        if behavior.get("name") == SITESHIELD_BEHAVIOR_NAME:
           siteshield_map = behavior['options']['ssmap']['value']
           break

    return siteshield_map


def extract_active_akamai_redirect_policy_versions(policy_tree):
    list_of_activations = []
    for activation in policy_tree["activations"]:
        if activation["policyInfo"]["status"] == 'active':
            list_of_activations.append({
                "policyId": str(policy_tree["policyId"]),
                "network": activation["network"],
                "groupId": str(policy_tree["groupId"]),
                "name": policy_tree["name"],
                "description": policy_tree["description"],
                "createdBy": policy_tree["createdBy"],
                "lastModifiedBy": policy_tree["lastModifiedBy"],
                "version": str(activation["policyInfo"]["version"]) or "0",
                "status": activation["policyInfo"]["status"],
                "activatedBy": activation["policyInfo"]["activatedBy"]
            })

    if len(list_of_activations) == 0:
        logger.info("Policy had no active occurrences. Candidate for cleanup: Policy ID %s", policy_tree["policyId"])

    return list(keep_first(list_of_activations, lambda d: (d['network'], d['policyId'])))


def search_akamai_ruleset_for_inbound_hosts(rule_tree):
    inbound_hosts = set()
    for block in rule_tree:
        try:
            if block["matchURL"]:
                inbound_hosts.update(urlparse(block["matchURL"]).netloc)
            else:
                for match in block["matches"]:
                    if match["matchType"] == "hostname":
                        inbound_hosts.update(match["matchValue"].split())
                    elif match["matchType"] == "clientip":
                        logger.info("NOTICE found IP allow list: %s", block)
        except Exception:
            logger.info("Skipping: %s", block)

    return [{"name": host} for host in set(inbound_hosts)]


def search_akamai_ruleset_for_outbound_hosts(rule_tree):
    outbound_hosts = set()
    for block in rule_tree:
        try:
            outbound_host = urlparse(block["redirectURL"]).netloc
            find = re.compile(r"(\\\d+)")
            if outbound_host != '' and not find.search(outbound_host):
                outbound_hosts.update(host for host in outbound_host.split())

        except Exception:
            logger.info("Skipping: %s", block)

    return [{"name": host} for host in set(outbound_hosts)]


class AkamaiApiClient:
    def __init__(self, base_url, client_token, client_secret, access_token, account_key = None):
        self.base_url = base_url
        self.error_count = 0
        self.page_size = 100
        self.session = resilient_session_factory()
        self.session.auth = EdgeGridAuth(
            client_token=client_token,
            client_secret=client_secret,
            access_token=access_token,
            max_body=128 * 1024,  # TODO: Completely Arbitrary Currently
        )
        self.account_key = account_key

    def _get_api_from_relative_path(self, path, params=None, headers=None):
        full_url = urljoin(self.base_url, path)
        logger.info("Exec: %s", full_url)

        # Insert account switch key
        if self.account_key is not None:
            if params is None:
                params = {}
            params['accountSwitchKey'] = self.account_key

        for sleepy_seconds in range(5):
            if sleepy_seconds:
                time.sleep(sleepy_seconds)
            response = self.session.get(full_url, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            self.error_count += 1
            logger.error(
                "response.status_code: %s, response.text: %s",
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise Exception(f"response.status_code: {response.status_code}", response.text)
    
    def _post_api_from_relative_path(self, path, body, params=None, headers=None):
        full_url = urljoin(self.base_url, path)
        logger.info("Exec: %s", full_url)

        # Insert account switch key
        if self.account_key is not None:
            if params is None:
                params = {}
            params['accountSwitchKey'] = self.account_key

        request_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        if isinstance(headers, dict):
            for header in headers.keys():
                request_headers[header] = headers[header]

        for sleepy_seconds in range(5):
            if sleepy_seconds:
                time.sleep(sleepy_seconds)
            response = self.session.post(full_url, params=params, headers=request_headers, json=body)
            if response.status_code == 200:
                return response.json()
            self.error_count += 1
            logger.error(
                "response.status_code: %s, response.text: %s",
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise Exception(f"response.status_code: {response.status_code}", response.text)

    def contracts_by_group(self) -> List[Tuple[str, str]]:
        groups_list_api_path = "/papi/v1/groups"
        response_json = self._get_api_from_relative_path(groups_list_api_path)
        return [
            (group["groupId"], contract_id)
            for group in response_json["groups"]["items"]
            for contract_id in group["contractIds"]
        ]

    def property_ids_for_contract_group(
        self, group_id: str, contract_id: str
    ) -> List[str]:
        property_list_api_path = "/papi/v1/properties"
        query_params = {
            "groupId": group_id,
            "contractId": contract_id,
        }
        response_json = self._get_api_from_relative_path(
            property_list_api_path, params=query_params
        )
        return [
            property["propertyId"] for property in response_json["properties"]["items"]
        ]

    def cloudlet_policy_ids(self) -> List[int]:
        cloudlet_list_api_path = "/cloudlets/api/v2/policies"
        offset = 0
        returned_policies = []
        page_size = 1000
        continue_query = True
        while continue_query:
            query_params = {"offset": offset}
            response_json = self._get_api_from_relative_path(
                cloudlet_list_api_path, params=query_params
            )
            returned_policies = returned_policies + response_json
            offset += page_size
            continue_query = len(response_json) == page_size

        return {policy["policyId"] for policy in returned_policies}
    
    def list_cloudlets_v2(self) -> List[int]:
        cloudlet_list_api_path = "/cloudlets/api/v2/policies"
        offset = 0
        returned_policies = []
        page_size = 1000
        continue_query = True
        while continue_query:
            query_params = {"offset": offset}
            response_json = self._get_api_from_relative_path(
                cloudlet_list_api_path, params=query_params
            )
            returned_policies = returned_policies + response_json
            offset += page_size
            continue_query = len(response_json) == page_size

        return returned_policies

    def extract_akamai_ruleset_version(self, policy_id: str, version: str):
        policy_tree_api_path = (
            f"/cloudlets/api/v2/policies/{policy_id}/versions/{version}"
        )
        match_rules = self._get_api_from_relative_path(policy_tree_api_path)["matchRules"]
        return match_rules


    def describe_policy_id(self, policy_id: str):
        policy_tree_api_path = (
            f"/cloudlets/api/v2/policies/{policy_id}"
        )
        return self._get_api_from_relative_path(policy_tree_api_path)

    def get_policy_rule_set(self, policy):
        policy_list = []
        try:
            policy_detail = extract_active_akamai_redirect_policy_versions(policy)
            for policy in policy_detail:
                if policy["version"] != "0":
                    raw_ruleset = self.extract_akamai_ruleset_version(policy["policyId"], policy["version"])
                    policy["id"] = f"akamai_redirect:{policy['policyId']}"
                    policy["inbound_hosts"] = search_akamai_ruleset_for_inbound_hosts(raw_ruleset)
                    policy["outbound_hosts"] = search_akamai_ruleset_for_outbound_hosts(raw_ruleset)
                    policy_list.append(policy)
        except Exception:
            logger.info("No version found in: %s", policy["policyId"])

        return policy_list
    
    def get_rule_tree(self, property_id: str, version: int):
        rule_tree_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/rules"
        )
        return self._get_api_from_relative_path(rule_tree_api_path)["rules"]

    def describe_property_hostnames(self, property_id: str, version: int):
        hosts_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/hostnames"
        )
        hosts_api_response = self._get_api_from_relative_path(hosts_api_path)
        return [
            EdgeHost(name=edge_host["cnameFrom"])
            for edge_host in hosts_api_response["hostnames"]["items"]
        ]

    def pull_host_entries(self, property_id: str, versions: set):
        origins = set()
        edge_redirector_policies = set()
        hostnames = set()
        for version in versions:
            if version is None:
                continue
            rule_tree = self.get_rule_tree(property_id, version)
            origins.update(search_akamai_rule_tree_for_origins(rule_tree))
            edge_redirector_policies.update()
            hostnames.update(self.describe_property_hostnames(property_id, version))
        return origins, edge_redirector_policies, hostnames

    def describe_property_by_id(self, property_id: str) -> PropertyDescription:
        describe_property_api_path = f"/papi/v1/properties/{property_id}"
        property_description = self._get_api_from_relative_path(
            describe_property_api_path
        )["properties"]["items"][0]
        property_name = property_description["propertyName"]
        production_version_number = property_description["productionVersion"]
        staging_version_number = property_description["stagingVersion"]
        origins, hostnames = self.pull_host_entries(property_id, {production_version_number, staging_version_number})

        return PropertyDescription(
            id=property_id, name=property_name, origins=list(origins), hostnames=list(hostnames)
        )
    
    def describe_property_by_dict(self, property: dict) -> PropertyDescription:
        origins = set()
        edge_redirector_policies = set()
        hostnames = set()
        
        rule_tree = self.get_rule_tree(property['propertyId'], property['latestVersion'])

        origins.update(search_akamai_rule_tree_for_origins(rule_tree))
        edge_redirector_policies.update(search_akamai_rule_tree_for_edge_redirector(rule_tree))
        hostnames.update(self.describe_property_hostnames(property['propertyId'], property['latestVersion']))

        return PropertyDescription(
            id=property['propertyId'],
            name=property['propertyName'],
            version=property['latestVersion'],
            origins=list(origins),
            edge_redirector_policies=list(edge_redirector_policies),
            hostnames=list(hostnames)
        )
    
    def search_all_properties(self):
        query = '$.name'
        search_path = '/papi/v1/bulk/rules-search-requests-synch'
        request_body = {
            'bulkSearchQuery': {
                'syntax': 'JSONPATH',
                'match': query
            } 
        }
        return self._post_api_from_relative_path(path=search_path, body=request_body)
    
    def list_all_properties(self):
        try:
            search = self.search_all_properties()
        except Exception as err:
            logger.info("Failed to search for properties: %s", err)
            return
        
        raw_property_ids = [p['propertyId'] for p in search['results']]
        # DeDupe list
        property_ids = list(set(raw_property_ids))
        results = []
        for property_id in property_ids:
            matching_properties = [p for p in search['results'] if p['propertyId'] == property_id]
            sorted_matching_properties = sorted(matching_properties, key=lambda d: d['propertyVersion'], reverse=True) 
            latest_property_version = sorted_matching_properties[0]
            production_version = None
            staging_version = None

            # Determine production version
            production_property_version = [p for p in sorted_matching_properties if p['productionStatus'] == 'ACTIVE']
            if len(production_property_version) > 0:
                production_version = production_property_version[0]['propertyVersion']

            # Determine staging version
            staging_property_version = [p for p in sorted_matching_properties if p['stagingStatus'] == 'ACTIVE']
            if len(staging_property_version) > 0:
                staging_version = staging_property_version[0]['propertyVersion']

            result_property = {
                'propertyId': latest_property_version['propertyId'],
                'propertyName': latest_property_version['propertyName'],
                'propertyType': latest_property_version['propertyType'],
                'latestVersion': latest_property_version['propertyVersion'],
                'stagingVersion': staging_version,
                'productionVersion': production_version
            }

            results.append(result_property)

        return results
        
    ## GTM functions
    def list_gtm_domains(self):
        gtm_domains_path = "/config-gtm/v1/domains"
        return self._get_api_from_relative_path(gtm_domains_path)['items']
    
    def get_gtm_domain(self, domain_name: str):
        gtm_domain_path = (
            f"/config-gtm/v1/domains/{domain_name}"
        )
        return self._get_api_from_relative_path(gtm_domain_path, headers = {'accept': 'application/vnd.config-gtm.v1.5+json'})
    
    ## Netstorage Functions
    def list_netstorage_groups(self):
        netstorage_groups_path = "/storage/v1/storage-groups"
        return self._get_api_from_relative_path(netstorage_groups_path)['items']
    
    ## AppSec Functions
    def get_appsec_hostname_coverage(self):
        hostname_coverage_path = "/appsec/v1/hostname-coverage"
        return self._get_api_from_relative_path(hostname_coverage_path)['hostnameCoverage']
    
    def list_appsec_configs(self):
        appsec_configs_path = '/appsec/v1/configs'
        return self._get_api_from_relative_path(appsec_configs_path)['configurations']
    
    def list_appsec_policies(self, configId, version):
        appsec_configs_path = '/appsec/v1/configs/{configId}/versions/{versionNumber}/security-policies'.format(configId = configId, versionNumber = version)
        return self._get_api_from_relative_path(appsec_configs_path)['policies']
    
    def export_appsec_config(self, config_id: int, config_version: int):
        export_config_path = f'/appsec/v1/export/configs/{config_id}/versions/{config_version}'
        return self._get_api_from_relative_path(export_config_path)
    
    ## SiteShield Functions
    def list_siteshield_maps(self):
        siteshield_maps_path = "/siteshield/v1/maps"
        return self._get_api_from_relative_path(siteshield_maps_path)['siteShieldMaps']

    ## EHN Functions
    def list_edge_hostnames(self):
        list_ehn_path = "/hapi/v1/edge-hostnames"
        return self._get_api_from_relative_path(list_ehn_path)['edgeHostnames']
    
    ## CPS Functions
    def list_cps_enrollments(self):
        list_enrollments_path = "/cps/v2/enrollments"
        headers = {
            'accept': 'application/vnd.akamai.cps.enrollments.v11+json'
        }
        return self._get_api_from_relative_path(list_enrollments_path, headers=headers)['enrollments']
    
    def get_cps_production_deployment(self, enrollment_id):
        cps_deployment_path = f"/cps/v2/enrollments/{enrollment_id}/deployments"
        headers = {
            'accept': 'application/vnd.akamai.cps.deployments.v7+json'
        }
        return self._get_api_from_relative_path(cps_deployment_path, headers=headers)['production']