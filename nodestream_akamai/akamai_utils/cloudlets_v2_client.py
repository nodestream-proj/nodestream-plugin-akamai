import logging
import re
from typing import List
from urllib.parse import urlparse

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiCloudletsV2Client(AkamaiApiClient):
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

    def cloudlet_policy_ids_er(self) -> List[int]:
        cloudlet_list_api_path = "/cloudlets/api/v2/policies?cloudletId=0"
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
        match_rules = self._get_api_from_relative_path(policy_tree_api_path)[
            "matchRules"
        ]
        return match_rules

    def describe_policy_id(self, policy_id: str):
        policy_tree_api_path = f"/cloudlets/api/v2/policies/{policy_id}"
        return self._get_api_from_relative_path(policy_tree_api_path)

    def extract_active_akamai_redirect_policy_versions(self, policy_tree):
        list_of_activations = []
        for activation in policy_tree["activations"]:
            if activation["policyInfo"]["status"] == "active":
                list_of_activations.append(
                    {
                        "policyId": policy_tree["policyId"],
                        "network": activation["network"],
                        "groupId": str(policy_tree["groupId"]),
                        "name": policy_tree["name"],
                        "description": policy_tree["description"],
                        "createdBy": policy_tree["createdBy"],
                        "lastModifiedBy": policy_tree["lastModifiedBy"],
                        "version": str(activation["policyInfo"]["version"]) or "0",
                        "status": activation["policyInfo"]["status"],
                        "activatedBy": activation["policyInfo"]["activatedBy"],
                    }
                )

        if len(list_of_activations) == 0:
            logger.info(
                "Policy had no active occurrences. Candidate for cleanup: Policy ID %s",
                policy_tree["policyId"],
            )

        # return list(self.keep_first(list_of_activations, lambda d: (d["network"], d["policyId"])))
        return list_of_activations

    def get_policy_rule_set(self, policy):
        policy_list = []
        try:
            policy_detail = self.extract_active_akamai_redirect_policy_versions(policy)
            for policy in policy_detail:
                if policy["version"] != "0":
                    raw_ruleset = self.extract_akamai_ruleset_version(
                        policy["policyId"], policy["version"]
                    )
                    policy["id"] = f"akamai_redirect:{policy['policyId']}"
                    policy[
                        "inbound_hosts"
                    ] = self.search_akamai_ruleset_for_inbound_hosts(raw_ruleset)
                    policy[
                        "outbound_hosts"
                    ] = self.search_akamai_ruleset_for_outbound_hosts(raw_ruleset)
                    policy_list.append(policy)
        except Exception as e:
            logger.info("No version found in: %s", policy["policyId"])
            logger.info(e)
            logger.info(policy)
        return policy_list

    def search_akamai_ruleset_for_inbound_hosts(self, rule_tree):
        inbound_hosts = set()
        inbound_hosts = []
        for block in rule_tree:
            try:
                if block["matchURL"]:
                    inbound_hosts.append(urlparse(block["matchURL"]).netloc)
                else:
                    for match in block["matches"]:
                        if match["matchType"] == "hostname":
                            inbound_hosts.append(match["matchValue"])
                        elif match["matchType"] == "clientip":
                            logger.info("NOTICE found IP allow list: %s", block)
            except Exception:
                logger.info("Skipping: %s", block)

        inbound_hosts = list(set(inbound_hosts))
        logger.info("-------------------------------------------------------------")
        logger.info(inbound_hosts)
        return [{"name": host} for host in set(inbound_hosts)]

    def search_akamai_ruleset_for_outbound_hosts(self, rule_tree):
        outbound_hosts = set()
        for block in rule_tree:
            try:
                outbound_host = urlparse(block["redirectURL"]).netloc
                find = re.compile(r"(\\\d+)")
                if outbound_host != "" and not find.search(outbound_host):
                    outbound_hosts.update(host for host in outbound_host.split())

            except Exception:
                logger.info("Skipping: %s", block)

        return [{"name": host} for host in set(outbound_hosts)]
