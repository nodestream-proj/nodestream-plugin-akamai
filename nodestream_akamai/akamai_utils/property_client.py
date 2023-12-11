import logging
from typing import List, Tuple

from jsonpath_ng.ext import parse

from .client import AkamaiApiClient
from .model import EdgeHost, Origin, PropertyDescription

logger = logging.getLogger(__name__)


class AkamaiPropertyClient(AkamaiApiClient):
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
            origins.update(self.search_akamai_rule_tree_for_origins(rule_tree))
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
            property["propertyId"], property["latestVersion"]
        )

        # Update origins
        origins = set()
        origins.update(self.search_akamai_rule_tree_for_origins(rule_tree))

        # Update hostnames
        hostnames = set()
        hostnames.update(
            self.describe_property_hostnames(
                property["propertyId"], property["latestVersion"]
            )
        )

        # Update cloudlets
        cloudlet_policies = {"edgeRedirector": set()}
        cloudlet_policies["edgeRedirector"].update(
            self.search_akamai_rule_tree_for_cloudlet(
                rule_tree=rule_tree, behavior_name="edgeRedirector"
            )
        )
        cloudlet_policies["edgeRedirector"] = list(cloudlet_policies["edgeRedirector"])

        return PropertyDescription(
            id=property["propertyId"],
            name=property["propertyName"],
            version=property["latestVersion"],
            origins=list(origins),
            cloudlet_policies=cloudlet_policies,
            hostnames=list(hostnames),
        )

    def search_all_properties(self):
        query = "$.name"
        search_path = "/papi/v1/bulk/rules-search-requests-synch"
        request_body = {"bulkSearchQuery": {"syntax": "JSONPATH", "match": query}}
        return self._post_api_from_relative_path(path=search_path, body=request_body)

    def list_all_properties(self):
        try:
            search = self.search_all_properties()
        except Exception as err:
            logger.info("Failed to search for properties: %s", err)
            return

        raw_property_ids = [p["propertyId"] for p in search["results"]]
        # DeDupe list
        property_ids = list(set(raw_property_ids))
        results = []
        for property_id in property_ids:
            matching_properties = [
                p for p in search["results"] if p["propertyId"] == property_id
            ]
            sorted_matching_properties = sorted(
                matching_properties, key=lambda d: d["propertyVersion"], reverse=True
            )
            latest_property_version = sorted_matching_properties[0]
            production_version = None
            staging_version = None

            # Determine production version
            production_property_version = [
                p
                for p in sorted_matching_properties
                if p["productionStatus"] == "ACTIVE"
            ]
            if len(production_property_version) > 0:
                production_version = production_property_version[0]["propertyVersion"]

            # Determine staging version
            staging_property_version = [
                p for p in sorted_matching_properties if p["stagingStatus"] == "ACTIVE"
            ]
            if len(staging_property_version) > 0:
                staging_version = staging_property_version[0]["propertyVersion"]

            result_property = {
                "propertyId": latest_property_version["propertyId"],
                "propertyName": latest_property_version["propertyName"],
                "propertyType": latest_property_version["propertyType"],
                "latestVersion": latest_property_version["propertyVersion"],
                "stagingVersion": staging_version,
                "productionVersion": production_version,
            }

            results.append(result_property)

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

    def search_akamai_rule_tree_for_cloudlet(self, rule_tree, behavior_name):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, behavior_name)
        policy_ids = []
        for behavior in instances:
            if behavior["options"].get("isSharedPolicy"):
                policy_id = behavior["options"]["cloudletSharedPolicy"]
            else:
                policy_id = behavior["options"]["cloudletPolicy"]["id"]
            policy_ids.append(str(policy_id))

        return list(set(policy_ids))

    def search_akamai_rule_tree_for_siteshield(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "siteShield")
        return instances[0]["options"]["ssmap"]["value"]

    def search_akamai_rule_tree_for_ivmi(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "imageManager")
        policy_sets = []
        for behavior in instances:
            policy_sets.append(behavior["options"]["policySet"])

        return list(set(policy_sets))

    def search_akamai_rule_tree_for_ivmv(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(
            rule_tree, "imageManagerVideo"
        )
        policy_sets = []
        for behavior in instances:
            policy_sets.append(behavior["options"]["policySet"])

        return list(set(policy_sets))

    def search_akamai_rule_tree_for_edge_workers(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "edgeWorker")
        ew_ids = []
        for behavior in instances:
            ew_ids.append(behavior["options"]["edgeWorkerId"])

        return list(set(ew_ids))
