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
    def __init__(self, base_url, client_token, client_secret, access_token):
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

    def _get_api_from_relative_path(self, path, params=None):
        full_url = urljoin(self.base_url, path)
        logger.info("Exec: %s", full_url)
        for sleepy_seconds in range(5):
            if sleepy_seconds:
                time.sleep(sleepy_seconds)
            response = self.session.get(full_url, params=params)
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

    def describe_property_origins(self, property_id: str, version: int):
        rule_tree_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/rules"
        )
        rule_tree = self._get_api_from_relative_path(rule_tree_api_path)["rules"]
        return search_akamai_rule_tree_for_origins(rule_tree)

    def describe_property_edge_hosts(self, property_id: str, version: int):
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
        edge_hosts = set()
        for version in versions:
            if version is None:
                continue
            origins.update(self.describe_property_origins(property_id, version))
            edge_hosts.update(self.describe_property_edge_hosts(property_id, version))
        return origins, edge_hosts

    def describe_property_by_id(self, property_id: str) -> PropertyDescription:
        describe_property_api_path = f"/papi/v1/properties/{property_id}"
        property_description = self._get_api_from_relative_path(
            describe_property_api_path
        )["properties"]["items"][0]
        property_name = property_description["propertyName"]
        production_version_number = property_description["productionVersion"]
        staging_version_number = property_description["stagingVersion"]
        origins, edge_hosts = self.pull_host_entries(property_id, {production_version_number, staging_version_number})

        return PropertyDescription(
            id=property_id, name=property_name, origins=list(origins), edge_hosts=list(edge_hosts)
        )
