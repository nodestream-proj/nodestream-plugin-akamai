import itertools
import logging
import re
from typing import Any, List, Tuple

from jsonpath_ng.ext import parse

from .client import AkamaiApiClient
from .model import EdgeHost, Origin, PropertyDescription

PATH_AND = " AND "

logger = logging.getLogger(__name__)


CLOUDLET_TYPES = [
    "applicationLoadBalancer",
    "apiPrioritization",
    "audienceSegmentation",
    "phasedRelease",
    "edgeRedirector",
    "forwardRewrite",
    "requestControl",
    "visitorPrioritization",
    "virtualWaitingRoom",
]

# Define criteria to look at
MATCH_TYPES = ["path", "hostname", "cloudletsOrigin"]

# Define negative criterion matches
NEGATIVE_OPERATORS = ["DOES_NOT_MATCH_ONE_OF", "IS_NOT_ONE_OF"]


def _get_policy_set_prefix(options):
    if "policyTokenDefault" in options:
        policy_set_prefix = options["policyTokenDefault"] + "-"
    elif "policyToken" in options:
        policy_set_prefix = options["policyToken"] + "-"
    else:
        policy_set_prefix = ""
    return policy_set_prefix


def _extract_origin(behavior):
    if behavior.get("name") == "origin":
        origin_options = behavior["options"]
        match origin_options.get("originType"):
            case "CUSTOMER":
                return Origin(name=origin_options.get("hostname"))
            case "NET_STORAGE":
                return Origin(
                    name=origin_options["netStorage"].get("downloadDomainName")
                )
            case "MEDIA_SERVICE_LIVE":
                return Origin(name=origin_options.get("mslorigin"))
            case _:
                return None
    return None


def _flatten_origins(origin):
    flattened = list(
        itertools.chain(
            (
                Origin(name=origin["name"], path=path)
                for path in origin.get("paths", [])
            ),
            (
                Origin(name=origin["name"], hostname=hostname)
                for hostname in origin.get("hostnames", [])
            ),
            (
                Origin(name=origin["name"], conditional_origin=conditional_origin)
                for conditional_origin in origin.get("conditional_origins", [])
            ),
        )
    )
    if flattened:
        return flattened

    return [Origin(name=origin["name"])]


class AkamaiPropertyClient(AkamaiApiClient):
    def __init__(
        self,
        base_url,
        client_token,
        client_secret,
        access_token,
        account_key=None,
    ):
        super().__init__(
            base_url,
            client_token,
            client_secret,
            access_token,
            account_key,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def headers(self):
        return {"PAPI-Use-Prefixes": "false"}

    def contracts_by_group(self) -> List[Tuple[str, str]]:
        groups_list_api_path = "/papi/v1/groups"
        response_json = self._get_api_from_relative_path(
            groups_list_api_path, headers=self.headers
        )
        return [
            (group["groupId"], contract_id)
            for group in response_json["groups"]["items"]
            for contract_id in group["contractIds"]
        ]

    def list_contracts(self) -> List[str]:
        contracts_list_api_path = "/papi/v1/contracts"
        response_json = self._get_api_from_relative_path(
            contracts_list_api_path, headers=self.headers
        )
        return response_json["contracts"]["items"]

    def property_ids_for_contract_group(
        self, group_id: str, contract_id: str
    ) -> List[str]:
        property_list_api_path = "/papi/v1/properties"
        query_params = {
            "groupId": group_id,
            "contractId": contract_id,
        }
        response_json = self._get_api_from_relative_path(
            property_list_api_path, params=query_params, headers=self.headers
        )
        return [prop["propertyId"] for prop in response_json["properties"]["items"]]

    def get_rule_tree(
        self, property_id: str, version: int, contract_id=None, group_id=None
    ):
        rule_tree_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/rules"
        )
        params = {}
        if contract_id is not None and group_id is not None:
            params = {"contractId": contract_id, "groupId": group_id}
        return self._get_api_from_relative_path(
            rule_tree_api_path, params=params, headers=self.headers
        )

    def get_property(self, property_id: str, contract_id=None, group_id=None):
        property_path = f"/papi/v1/properties/{property_id}"
        params = {}
        if contract_id is not None and group_id is not None:
            params = {"contractId": contract_id, "groupId": group_id}
        return self._get_api_from_relative_path(
            property_path, params=params, headers=self.headers
        )["properties"]["items"][0]

    def describe_property_hostnames(
        self, property_id: str, version: int, contract_id=None, group_id=None
    ):
        hosts_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/hostnames"
        )
        params = {}
        if contract_id is not None and group_id is not None:
            params = {"contractId": contract_id, "groupId": group_id}
        hosts_api_response = self._get_api_from_relative_path(
            hosts_api_path, params=params, headers=self.headers
        )
        return [
            EdgeHost(name=edge_host["cnameFrom"])
            for edge_host in hosts_api_response["hostnames"]["items"]
        ]

    def pull_host_entries(
        self, property_id: str, versions: set
    ) -> tuple[set[Origin], set[Any], set[EdgeHost]]:
        origins = set()
        edge_redirector_policies = set()
        hostnames = set()
        for version in versions:
            if version is None:
                continue
            rule_tree = self.get_rule_tree(property_id, version)
            origins.update(self.search_akamai_rule_tree_for_origins(rule_tree))
            edge_redirector_policies.update()
            hostnames.update(self.describe_property_hostnames(property_id, version))
        return origins, edge_redirector_policies, hostnames

    def describe_property_by_id(self, property_id: str) -> PropertyDescription:
        describe_property_api_path = f"/papi/v1/properties/{property_id}"
        property_description = self._get_api_from_relative_path(
            describe_property_api_path, headers=self.headers
        )["properties"]["items"][0]
        property_name = property_description["propertyName"]
        production_version_number = property_description["productionVersion"]
        staging_version_number = property_description["stagingVersion"]
        origins, _, hostnames = self.pull_host_entries(
            property_id, {production_version_number, staging_version_number}
        )

        return PropertyDescription(
            id=property_id,
            name=property_name,
            origins=list(origins),
            hostnames=list(hostnames),
        )

    def describe_property_by_dict(self, prop: dict) -> PropertyDescription:
        # Get rule tree
        rule_tree = self.get_rule_tree(
            property_id=prop["propertyId"],
            version=prop["latestVersion"],
            contract_id=prop["contractId"],
            group_id=prop["groupId"],
        )
        rule_tree["assetId"] = prop["assetId"]

        # Update origins
        origins = self.collate_origins_with_criteria(rule_tree["rules"])
        hostnames = prop["hostnames"]

        # Cloudlets
        cloudlet_policies = self.search_akamai_rule_tree_for_cloudlets(
            rule_tree=rule_tree["rules"]
        )

        # Specific data for Edge Redirector, flter for legacy only
        edge_redirector_policies = self.search_akamai_rule_tree_for_cloudlet(
            rule_tree=rule_tree["rules"], behavior_name="edgeRedirector", shared=False
        )

        # IVM
        image_manager_policysets = self.search_akamai_rule_tree_for_ivm(
            rule_tree=rule_tree
        )

        # EdgeWorkers
        edgeworker_ids = self.search_akamai_rule_tree_for_edge_workers(
            rule_tree=rule_tree["rules"]
        )

        # Siteshield
        siteshield_maps = self.search_akamai_rule_tree_for_siteshield(
            rule_tree=rule_tree["rules"]
        )

        # Siteshield
        cp_codes = self.search_akamai_rule_tree_for_cp_codes(
            rule_tree=rule_tree["rules"]
        )

        # Deeplink
        deeplink_prefix = (
            "https://control.akamai.com/apps/property-manager/#/property-version/"
        )
        deeplink = "{prefix}{assetId}/{version}/edit?gid={groupId}".format(
            prefix=deeplink_prefix,
            assetId=prop["assetId"],
            version=prop["latestVersion"],
            groupId=prop["groupId"],
        )

        return PropertyDescription(
            id=prop["propertyId"],
            name=prop["propertyName"],
            version=prop["latestVersion"],
            rule_format=rule_tree["ruleFormat"],
            origins=origins,
            cloudlet_policies=cloudlet_policies,
            edge_redirector_policies=edge_redirector_policies,
            image_manager_policysets=image_manager_policysets,
            edgeworker_ids=edgeworker_ids,
            siteshield_maps=siteshield_maps,
            hostnames=hostnames,
            deeplink=deeplink,
            cp_codes=cp_codes,
        )

    def search_all_properties(self):
        query = "$.name"
        search_path = "/papi/v1/bulk/rules-search-requests-synch"
        request_body = {"bulkSearchQuery": {"syntax": "JSONPATH", "match": query}}
        return self._post_api_from_relative_path(path=search_path, body=request_body)

    def list_account_hostnames(self, network="PRODUCTION"):
        list_hostnames_path = f"/papi/v1/hostnames?network={network}&offset=0&limit=999"
        result = self._get_api_from_relative_path(path=list_hostnames_path)
        hostnames = result["hostnames"]["items"]
        while "nextLink" in result["hostnames"]:
            next_link = result["hostnames"]["nextLink"]
            result = self._get_api_from_relative_path(path=next_link)
            hostnames.extend(result["hostnames"]["items"])

        return hostnames

    def list_all_properties(self):
        try:
            hostnames = self.list_account_hostnames()
        except Exception as err:
            logger.exception("Failed to list property hostnames: %s", err)
            return None

        property_ids = {h["propertyId"] for h in hostnames}
        # DeDupe list
        return [
            self._get_property_response(property_id, hostnames)
            for property_id in property_ids
        ]

    def search_akamai_rule_tree_for_origins(self, rule_tree) -> set[Origin]:
        behaviors = rule_tree.get("behaviors", [])
        children = rule_tree.get("children", [])
        origins = set()

        for child_rule_tree in children:
            for child_origin in self.search_akamai_rule_tree_for_origins(
                child_rule_tree
            ):
                origins.add(child_origin)

        for behavior in behaviors:
            extracted = _extract_origin(behavior)
            if extracted:
                origins.add(extracted)

        return set(origins)

    def collate_origins_with_criteria(self, rules) -> list[Origin]:
        """
        This function will find all Origin behaviours in a property and collate any relevant criteria
        into accompanying Lists.
        """
        jsonpath_expression = parse('$..behaviors[?(@.name=="origin")]')
        jsonpath_result = jsonpath_expression.find(rules)
        # Parse matched jsonpath behaviours
        origins = [
            self._jsonpath_fetch_origins(jsonpath_path, rules)
            for jsonpath_path in jsonpath_result
        ]

        # Expand to one origin hostname/path combo per object to simplify the pipeline config and avoid
        # nested looping

        return list(
            itertools.chain.from_iterable(
                _flatten_origins(origin) for origin in origins
            )
        )

    def _jsonpath_fetch_origins(self, jsonpath_path, rules):
        origin_host, location_elements = self.parse_origin_search(jsonpath_path, rules)
        parent_location = ""
        combined_rule_paths = []
        combined_rule_hosts = []
        combined_rule_cdids = []
        for location in location_elements:
            location_results = self.parse_origin_location(
                location, parent_location, rules
            )
            if len(location_results.get("path", [])) > 0:
                combined_rule_paths.append(location_results["path"])
            if len(location_results.get("hostname", [])) > 0:
                combined_rule_hosts.append(location_results["hostname"])
            if len(location_results.get("cloudOrigin", [])) > 0:
                combined_rule_cdids.append(location_results["cloudOrigin"])
            parent_location = location
        # Combine results into single list with boolean AND between parent and child
        output = {"name": origin_host}

        if combined_rule_paths:
            output["paths"] = [
                PATH_AND.join(path_product)
                for path_product in itertools.product(*combined_rule_paths)
            ]
        if combined_rule_hosts:
            output["hostnames"] = [
                PATH_AND.join(host_product)
                for host_product in itertools.product(*combined_rule_hosts)
            ]

        if combined_rule_cdids:
            output["conditional_origins"] = [
                PATH_AND.join(cdid_product)
                for cdid_product in itertools.product(*combined_rule_cdids)
            ]

        return output

    def parse_origin_search(self, path, rules):
        """
        This function parses jsonpath origin search results into a hostname
        and location elements List
        """
        self.logger.debug("parse_origin_search")
        origin_location = str(path.full_path)
        rule_base = re.sub(r"behaviors.\[\d+]", "", origin_location)
        origin_host = "ERROR"  # Host should be renamed

        # Extract origin behaviour itself and append hostname to list based on origin type
        origin_behavior_match = parse(origin_location)
        origin_search = origin_behavior_match.find(rules)
        origin_behavior = origin_search[0].value
        if "hostname" in origin_behavior["options"]:
            origin_host = origin_behavior["options"]["hostname"]
        elif "netStorage" in origin_behavior["options"]:
            origin_host = origin_behavior["options"]["netStorage"]["downloadDomainName"]
        elif "mslorigin" in origin_behavior["options"]:
            origin_host = origin_behavior["options"]["mslorigin"]

        # Split JSONPATH into children[X] elements so we can iterate down the path
        location_elements = re.findall(r"children\.\[\d+]", rule_base)
        return origin_host, location_elements

    def parse_origin_location(self, rule_location_input, parent_location, rules):
        """
        This function parses origin locations to extract path matches, hostname matches
        and Conditional Origin IDs
        """
        self.logger.debug(
            "parse_origin_location(rule_location=%s, parent_location=%s)",
            rule_location_input,
            parent_location,
        )
        # Construct rule location from element and optionally parent path
        if parent_location != "":
            rule_location = parent_location + "." + rule_location_input
        else:
            rule_location = rule_location_input

        rule_match = parse(rule_location)
        rule_search = rule_match.find(rules)

        if rule_search is None or len(rule_search) == 0:
            self.logger.warning("No rule found at position '%s'", rule_location)
            return {}

        # Extract rule by JSONPATH
        rule = rule_search[0].value

        # Instantiate results
        criteria_results = {}
        rule_results = {k: [] for k in MATCH_TYPES}
        location_results = {}

        for match_type in MATCH_TYPES:
            criteria_results[match_type] = []
            criterion_results = {k: [] for k in MATCH_TYPES}

            # Parse criteria and create list of lists of path matches
            for rule_criterion in rule["criteria"]:
                criterion_results[match_type] = []

                if rule_criterion["name"] == match_type:
                    rc_options = rule_criterion["options"]
                    for value in rc_options.get("values", []):
                        if rc_options.get("matchOperator") in NEGATIVE_OPERATORS:
                            value = "!" + value
                        criterion_results[match_type].append(value)

                if len(criterion_results[match_type]) > 0:
                    criteria_results[match_type].append(criterion_results[match_type])

            if len(criteria_results[match_type]) > 0:
                # Collate path matches into a list of combinations, based on criteria setting
                if len(criteria_results[match_type]) == 1:
                    rule_results[match_type] = criteria_results[match_type][0]
                else:
                    if rule["criteriaMustSatisfy"] == "all":
                        # If using ALL option we must create boolean combos
                        rule_product = itertools.product(*criteria_results[match_type])
                        for product in rule_product:
                            rule_results[match_type].append(" AND ".join(product))
                    else:
                        for result in criteria_results[match_type]:
                            rule_results[match_type].extend(result)

        return location_results

    def search_akamai_rule_tree_for_behavior(self, rule_tree, behavior_name):
        self.logger.debug(
            "search_akamai_rule_tree_for_behavior(behavior_name=%s)", behavior_name
        )
        jsonpath_expression = parse(
            '$..behaviors[?(@.name=="{b}")]'.format(b=behavior_name)
        )
        jsonpath_result = jsonpath_expression.find(rule_tree)

        return [match.value for match in jsonpath_result]

    def search_akamai_rule_tree_for_edge_redirector(self, rule_tree):
        return self.search_akamai_rule_tree_for_cloudlet(rule_tree, "edgeRedirector")

    def search_akamai_rule_tree_for_cloudlet(
        self, rule_tree, behavior_name, shared=None
    ):
        # If shared is None, both shared and legacy behaviors will be matched
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, behavior_name)
        policy_ids = []
        for behavior in instances:
            if behavior["options"]["enabled"]:
                if behavior["options"].get("isSharedPolicy"):
                    # Skip this if shared is False
                    if not shared:
                        continue
                    policy_id = behavior["options"]["cloudletSharedPolicy"]
                else:
                    # Skip this if shared is True
                    if shared:
                        continue
                    policy_id = behavior["options"]["cloudletPolicy"]["id"]
                policy_ids.append(policy_id)

        return list(set(policy_ids))

    def search_akamai_rule_tree_for_cloudlets(self, rule_tree):
        instances = []
        for cloudlet_type in CLOUDLET_TYPES:
            instances.extend(
                self.search_akamai_rule_tree_for_behavior(rule_tree, cloudlet_type)
            )
        policy_ids = []
        for behavior in instances:
            if behavior["options"]["enabled"]:
                if behavior["options"].get("isSharedPolicy"):
                    policy_id = behavior["options"]["cloudletSharedPolicy"]
                else:
                    policy_id = behavior["options"]["cloudletPolicy"]["id"]
                policy_ids.append(policy_id)

        return list(set(policy_ids))

    def search_akamai_rule_tree_for_siteshield(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "siteShield")
        return [siteshield["options"]["ssmap"]["value"] for siteshield in instances]

    def search_akamai_rule_tree_for_ivm(self, rule_tree):
        image_instances = self.search_akamai_rule_tree_for_behavior(
            rule_tree, "imageManager"
        )
        video_instances = self.search_akamai_rule_tree_for_behavior(
            rule_tree, "imageManagerVideo"
        )
        instances = image_instances + video_instances

        for instance in instances:
            # Need to work out policySet if using default or custom options
            options = instance["options"]
            if "policySet" not in options:
                policy_set_prefix = _get_policy_set_prefix(options)
                policy_set = f"{policy_set_prefix}{rule_tree['assetId']}"
                if instance["name"] == "imageManagerVideo":
                    policy_set += "-v"
                options["policySet"] = policy_set

        policy_sets = []
        for behavior in instances:
            policy_sets.append(behavior["options"]["policySet"])

        return list(set(policy_sets))

    def search_akamai_rule_tree_for_edge_workers(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "edgeWorker")
        ew_ids = []
        for behavior in instances:
            ew_ids.append(int(behavior["options"]["edgeWorkerId"]))

        return list(set(ew_ids))

    def search_akamai_rule_tree_for_cp_codes(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "cpCode")
        cpcode_ids = []
        for behavior in instances:
            if "value" in behavior["options"] and "id" in behavior["options"]["value"]:
                cpcode_ids.append(int(behavior["options"]["value"]["id"]))

        return list(set(cpcode_ids))

    def _get_property_response(self, property_id, hostnames):
        property_hostnames = [h for h in hostnames if h["propertyId"] == property_id]

        contract_id = property_hostnames[0]["contractId"]
        group_id = property_hostnames[0]["groupId"]

        try:
            property_response = self.get_property(
                property_id=property_id,
                contract_id=contract_id,
                group_id=group_id,
            )
        except Exception as err:
            logger.exception("Failed to get property %s: %s", property_id, err)
            return None

        property_response["hostnames"] = property_hostnames
        return property_response
