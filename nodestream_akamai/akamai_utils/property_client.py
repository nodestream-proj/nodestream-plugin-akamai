import logging
import re
from typing import List, Tuple

from jsonpath_ng.ext import parse

from .client import AkamaiApiClient
from .model import EdgeHost, Origin, PropertyDescription

logger = logging.getLogger(__name__)


class AkamaiPropertyClient(AkamaiApiClient):
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

    headers = {"PAPI-Use-Prefixes": "false"}

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
        return [
            property["propertyId"] for property in response_json["properties"]["items"]
        ]

    def get_rule_tree(
        self, property_id: str, version: int, contractId=None, groupId=None
    ):
        rule_tree_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/rules"
        )
        params = {}
        if contractId is not None and groupId is not None:
            params = {"contractId": contractId, "groupId": groupId}
        return self._get_api_from_relative_path(
            rule_tree_api_path, params=params, headers=self.headers
        )

    def get_property(self, property_id: str, contractId=None, groupId=None):
        property_path = f"/papi/v1/properties/{property_id}"
        params = {}
        if contractId is not None and groupId is not None:
            params = {"contractId": contractId, "groupId": groupId}
        return self._get_api_from_relative_path(
            property_path, params=params, headers=self.headers
        )["properties"]["items"][0]

    def describe_property_hostnames(
        self, property_id: str, version: int, contractId=None, groupId=None
    ):
        hosts_api_path = (
            f"/papi/v1/properties/{property_id}/versions/{version}/hostnames"
        )
        params = {}
        if contractId is not None and groupId is not None:
            params = {"contractId": contractId, "groupId": groupId}
        hosts_api_response = self._get_api_from_relative_path(
            hosts_api_path, params=params, headers=self.headers
        )
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
        origins, hostnames = self.pull_host_entries(
            property_id, {production_version_number, staging_version_number}
        )

        return PropertyDescription(
            id=property_id,
            name=property_name,
            origins=list(origins),
            hostnames=list(hostnames),
        )

    def describe_property_by_dict(self, property: dict) -> PropertyDescription:
        # Get rule tree
        rule_tree = self.get_rule_tree(
            property_id=property["propertyId"],
            version=property["latestVersion"],
            contractId=property["contractId"],
            groupId=property["groupId"],
        )
        rule_tree["assetId"] = property["assetId"]

        # Update origins
        origins = set()
        origins.update(self.search_akamai_rule_tree_for_origins(rule_tree["rules"]))

        # Update hostnames
        hostnames = set()
        hostnames.update(
            self.describe_property_hostnames(
                property_id=property["propertyId"],
                version=property["latestVersion"],
                contractId=property["contractId"],
                groupId=property["groupId"],
            )
        )

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

        return PropertyDescription(
            id=property["propertyId"],
            name=property["propertyName"],
            version=property["latestVersion"],
            ruleFormat=rule_tree["ruleFormat"],
            origins=list(origins),
            cloudlet_policies=cloudlet_policies,
            edge_redirector_policies=edge_redirector_policies,
            image_manager_policysets=image_manager_policysets,
            edgeworker_ids=edgeworker_ids,
            siteshield_maps=siteshield_maps,
            hostnames=list(hostnames),
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
        while "nextLink" in result["hostnames"].keys():
            next_link = result["hostnames"]["nextLink"]
            result = self._get_api_from_relative_path(path=next_link)
            hostnames.extend(result["hostnames"]["items"])

        return hostnames

    def list_all_properties(self):
        try:
            hostnames = self.list_account_hostnames()
        except Exception as err:
            logger.info("Failed to list property hostnames: %s", err)
            return

        raw_property_ids = [h["propertyId"] for h in hostnames]
        # DeDupe list
        property_ids = list(set(raw_property_ids))
        results = []
        for property_id in property_ids:
            matching_hostname = [
                h for h in hostnames if h["propertyId"] == property_id
            ][0]

            contract_id = matching_hostname["contractId"]
            group_id = matching_hostname["groupId"]

            try:
                property_response = self.get_property(
                    property_id=property_id,
                    contractId=contract_id,
                    groupId=group_id,
                )
            except Exception as err:
                logger.info(f"Failed to get property {property_id}: {err}")
                return

            results.append(property_response)

        return results

    def search_akamai_rule_tree_for_origins(self, rule_tree) -> List[Origin]:
        behaviors = rule_tree["behaviors"]
        children = rule_tree["children"]
        origins = [
            origin
            for child_rule_tree in children
            for origin in self.search_akamai_rule_tree_for_origins(child_rule_tree)
        ]
        for behavior in behaviors:
            if behavior.get("name") == "origin":
                origin_options = behavior["options"]
                hostname = origin_options.get("hostname")
                if hostname is not None:
                    origins.append(Origin(name=hostname))

        # TODO: Maybe find a less terrible way to get unique list of origins - check as you go?
        return list(set(origins))

    def collate_origins_with_criteria(self, rules):
        origins = []
        jsonpath_expression = parse('$..behaviors[?(@.name=="origin")]')
        jsonpath_result = jsonpath_expression.find(rules)
        for jsonpath_path in jsonpath_result:
            origin_location = str(jsonpath_path.full_path)
            rule_base = re.sub("\.behaviors.\[[\d]+\]", "", origin_location)
            path_matches = []

            reducing_path = rule_base
            while "children" in reducing_path:
                criteria_location = reducing_path + ".criteria"
                direct_criteria_match = parse(criteria_location)
                direct_criteria = direct_criteria_match.find(rules)
                for criteria in direct_criteria:
                    for criterion in criteria.value:
                        if criterion["name"] == "path":
                            if (
                                criterion["options"]["matchOperator"]
                                == "MATCHES_ONE_OF"
                            ):
                                path_matches.extend(criterion["options"]["values"])
                            elif (
                                criterion["options"]["matchOperator"]
                                == "DOES_NOT_MATCH_ONE_OF"
                            ):
                                for match in criterion["options"]["values"]:
                                    path_matches.append("!" + match)

                reducing_path = re.sub("\.children\.\[[\d]+\]$", "", reducing_path)

            origins.append({"location": origin_location, "path_matches": path_matches})

        return origins

    def search_akamai_rule_tree_for_behavior(self, rule_tree, behavior_Name):
        behaviors = []
        jsonpath_expression = parse(
            '$..behaviors[?(@.name=="{b}")]'.format(b=behavior_Name)
        )
        jsonpath_result = jsonpath_expression.find(rule_tree)
        for match in jsonpath_result:
            behaviors.append(match.value)
        return behaviors

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
                    if shared == False:
                        continue
                    policy_id = behavior["options"]["cloudletSharedPolicy"]
                else:
                    # Skip this if shared is True
                    if shared == True:
                        continue
                    policy_id = behavior["options"]["cloudletPolicy"]["id"]
                policy_ids.append(policy_id)

        return list(set(policy_ids))

    def search_akamai_rule_tree_for_cloudlets(self, rule_tree):
        instances = []
        for CLOUDLET_TYPE in self.CLOUDLET_TYPES:
            instances.extend(
                self.search_akamai_rule_tree_for_behavior(rule_tree, CLOUDLET_TYPE)
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
        map_names = [
            siteshield["options"]["ssmap"]["value"] for siteshield in instances
        ]
        return map_names

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
            if "policySet" not in instance["options"].keys():
                if "policyTokenDefault" in instance["options"].keys():
                    policy_set_prefix = instance["options"]["policyTokenDefault"]
                elif "policyToken" in instance["options"].keys():
                    policy_set_prefix = instance["options"]["policyToken"]

                policy_set = f"{policy_set_prefix}-{rule_tree['assetId']}"
                if instance["name"] == "imageManagerVideo":
                    policy_set += "-v"
                instance["options"]["policySet"] = policy_set

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
