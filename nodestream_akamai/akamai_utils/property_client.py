import itertools
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
        origins = self.collate_origins_with_criteria(rule_tree["rules"])
        hostnames = property["hostnames"]

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
            assetId=property["assetId"],
            version=property["latestVersion"],
            groupId=property["groupId"],
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
            property_hostnames = [
                h for h in hostnames if h["propertyId"] == property_id
            ]

            contract_id = property_hostnames[0]["contractId"]
            group_id = property_hostnames[0]["groupId"]

            try:
                property_response = self.get_property(
                    property_id=property_id,
                    contractId=contract_id,
                    groupId=group_id,
                )
            except Exception as err:
                logger.info(f"Failed to get property {property_id}: {err}")
                return

            property_response["hostnames"] = property_hostnames

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
                hostname = None
                if origin_options["originType"] == "CUSTOMER":
                    hostname = origin_options.get("hostname")
                elif origin_options["originType"] == "NET_STORAGE":
                    hostname = origin_options["netStorage"].get("downloadDomainName")
                elif origin_options["originType"] == "MEDIA_SERVICE_LIVE":
                    hostname = origin_options.get("mslorigin")
                if hostname is not None:
                    origins.append(Origin(name=hostname))

        # TODO: Maybe find a less terrible way to get unique list of origins - check as you go?
        return list(set(origins))

    def collate_origins_with_criteria(self, rules):
        """
        This function will find all Origin behaviours in a property and collate any relevant criteria
        into accompanying Lists.
        """
        origins = []
        jsonpath_expression = parse('$..behaviors[?(@.name=="origin")]')
        jsonpath_result = jsonpath_expression.find(rules)
        # Parse matched jsonpath behaviours
        for jsonpath_path in jsonpath_result:
            origin_host, location_elements = self.parse_origin_search(
                jsonpath_path, rules
            )
            parent_location = ""
            combined_rule_paths = []
            combined_rule_hosts = []
            combined_rule_cdids = []

            # for i in range(len(location_elements)):
            #     # Construct rule location from element and optionally parent path
            #     if parent_location == "":
            #         rule_location = location_elements[i]
            #     else:
            #         rule_location = parent_location + "." + location_elements[i]
            #     rule_match = parse(rule_location)
            #     rule_search = rule_match.find(rules)

            #     if len(rule_search) == 0:
            #         raise (Exception(f"No rule found at position '{rule_location}'"))

            #     # Extract rule by JSONPATH
            #     rule = rule_search[0].value
            #     criteria_paths = []
            #     criteria_hosts = []
            #     criteria_cdids = []

            #     # Parse criteria and create list of lists of path matches
            #     for criterion in rule["criteria"]:
            #         criterion_paths = []
            #         criterion_hosts = []
            #         criterion_cdids = []
            #         if criterion["name"] == "path":
            #             for match in criterion["options"]["values"]:
            #                 if (
            #                     criterion["options"]["matchOperator"]
            #                     == "DOES_NOT_MATCH_ONE_OF"
            #                 ):
            #                     match = "!" + match
            #                 criterion_paths.append(match)
            #         if criterion["name"] == "hostname":
            #             for match in criterion["options"]["values"]:
            #                 if criterion["options"]["matchOperator"] == "IS_NOT_ONE_OF":
            #                     match = "!" + match
            #                 criterion_hosts.append(match)
            #         if criterion["name"] == "cloudletsOrigin":
            #             criterion_cdids.append(criterion["options"["originId"]])
            #         if len(criterion_paths) > 0:
            #             criteria_paths.append(criterion_paths)
            #         if len(criterion_hosts) > 0:
            #             criteria_hosts.append(criterion_hosts)
            #         if len(criterion_paths) > 0:
            #             criteria_cdids.append(criterion_cdids)

            #     rule_paths = []
            #     rule_hosts = []
            #     rule_cdids = []
            #     if len(criteria_paths) > 0:
            #         # Collate path matches into a list of combinations, based on criteria setting
            #         if len(criteria_paths) == 1:
            #             rule_paths = criteria_paths[0]
            #         else:
            #             if rule["criteriaMustSatisfy"] == "all":
            #                 # If using ALL option we must create boolean combos
            #                 rule_paths_product = itertools.product(*criteria_paths)
            #                 for path_product in rule_paths_product:
            #                     rule_paths.append(" AND ".join(path_product))
            #             else:
            #                 for criteria_path in criteria_paths:
            #                     rule_paths.extend(criteria_path)

            #     if len(criteria_hosts) > 0:
            #         if len(criteria_hosts) == 1:
            #             rule_hosts = criteria_hosts[0]
            #         else:
            #             if rule["criteriaMustSatisfy"] == "all":
            #                 rule_hosts_product = itertools.product(*criteria_hosts)
            #                 for hosts_product in rule_hosts_product:
            #                     rule_hosts.append(" AND ".join(hosts_product))
            #             else:
            #                 for criteria_host in criteria_hosts:
            #                     rule_hosts.extend(criteria_host)

            #     if len(criteria_cdids) > 0:
            #         if len(criteria_cdids) == 1:
            #             rule_cdids = criteria_cdids[0]
            #         else:
            #             if rule["criteriaMustSatisfy"] == "all":
            #                 rule_cdids_product = itertools.product(*criteria_cdids)
            #                 for cdid_product in rule_cdids_product:
            #                     rule_cdids.append(" AND ".join(cdid_product))
            #             else:
            #                 for criteria_cdid in criteria_cdids:
            #                     rule_cdids.extend(criteria_cdid)

            #     # Hold onto combined variables so we can combine across parent and children at the end
            #     if len(rule_paths) > 0:
            #         combined_rule_paths.append(rule_paths)
            #     if len(rule_hosts) > 0:
            #         combined_rule_hosts.append(rule_hosts)
            #     if len(rule_cdids) > 0:
            #         combined_rule_cdids.append(rule_cdids)
            #     parent_location = rule_location

            for location in location_elements:
                location_results = self.parse_origin_location(
                    location, parent_location, rules
                )
                if len(location_results["path"]) > 0:
                    combined_rule_paths.append(location_results["path"])
                if len(location_results["hostname"]) > 0:
                    combined_rule_hosts.append(location_results["hostname"])
                if len(location_results["cloudOrigin"]) > 0:
                    combined_rule_cdids.append(location_results["cloudOrigin"])
                parent_location = location

            # Combine results into single list with boolean AND between parent and child
            origin_paths = []
            origin_paths_product = itertools.product(*combined_rule_paths)
            for path_product in origin_paths_product:
                origin_paths.append(" AND ".join(path_product))

            origin_hosts = []
            origin_hosts_product = itertools.product(*combined_rule_hosts)
            for host_product in origin_hosts_product:
                origin_hosts.append(" AND ".join(host_product))

            origin_cdids = []
            origin_cdids_product = itertools.product(*combined_rule_cdids)
            for cdid_product in origin_cdids_product:
                origin_cdids.append(" AND ".join(cdid_product))

            origins.append(
                {
                    "name": origin_host,
                    "paths": origin_paths,
                    "hostnames": origin_hosts,
                    "conditional_origins": origin_cdids,
                }
            )

        # Expand to one origin hostname/path combo per object to simplify the pipeline config and avoid
        # nested looping
        expanded_origins = []
        for origin in origins:
            for path in origin["paths"]:
                expanded_origins.append({"name": origin["name"], "path": path})
            for hostname in origin["hostnames"]:
                expanded_origins.append({"name": origin["name"], "hostname": hostname})
            for conditional_origin in origin["conditional_origins"]:
                expanded_origins.append(
                    {"name": origin["name"], "conditional_origin": conditional_origin}
                )

        return expanded_origins

    def parse_origin_search(self, path, rules):
        """
        This function parses jsonpath origin search results into a hostname
        and location elements List
        """
        origin_location = str(path.full_path)
        rule_base = re.sub("behaviors.\[[\d]+\]", "", origin_location)
        origin_host = "ERROR"  # Host should be renamed

        # Extract origin behaviour itself and append hostname to list based on origin type
        origin_behavior_match = parse(origin_location)
        origin_search = origin_behavior_match.find(rules)
        origin_behavior = origin_search[0].value
        if "hostname" in origin_behavior["options"].keys():
            origin_host = origin_behavior["options"]["hostname"]
        elif "netStorage" in origin_behavior["options"].keys():
            origin_host = origin_behavior["options"]["netStorage"]["downloadDomainName"]
        elif "mslorigin" in origin_behavior["options"].keys():
            origin_host = origin_behavior["options"]["mslorigin"]

        # Split JSONPATH into children[X] elements so we can iterate down the path
        location_elements = re.findall("children\.\[[\d]+\]", rule_base)
        return origin_host, location_elements

    def parse_origin_location(self, rule_location, parent_location, rules):
        """
        This function parses origin locations to extract path matches, hostname matches
        and Conditional Origin IDs
        """
        # Construct rule location from element and optionally parent path
        if parent_location != "":
            rule_location = parent_location + "." + rule_location
        rule_match = parse(rule_location)
        rule_search = rule_match.find(rules)

        if len(rule_search) == 0:
            raise (Exception(f"No rule found at position '{rule_location}'"))

        # Define criteria to look at
        match_types = ["path", "hostname", "cloudletsOrigin"]

        # Define negative criterion matches
        negative_operators = ["DOES_NOT_MATCH_ONE_OF", "IS_NOT_ONE_OF"]

        # Extract rule by JSONPATH
        rule = rule_search[0].value

        # Instantiate results
        criteria_results = {}
        rule_results = {}
        location_results = {}

        for match_type in match_types:
            criteria_results[match_type] = []
            criterion_results = {}

            # Parse criteria and create list of lists of path matches
            for rule_criterion in rule["criteria"]:
                criterion_results[match_type] = []

                if rule_criterion["name"] == match_type:
                    for value in rule_criterion["options"]["values"]:
                        if (
                            rule_criterion["options"]["matchOperator"]
                            in negative_operators
                        ):
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

    def search_akamai_rule_tree_for_cp_codes(self, rule_tree):
        instances = self.search_akamai_rule_tree_for_behavior(rule_tree, "cpCode")
        cpcode_ids = []
        for behavior in instances:
            if "value" in behavior["options"] and "id" in behavior["options"]["value"]:
                cpcode_ids.append(int(behavior["options"]["value"]["id"]))

        return list(set(cpcode_ids))
