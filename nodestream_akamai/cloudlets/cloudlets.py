import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.cloudlet_client import AkamaiCloudletClient


class AkamaiCloudletExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiCloudletClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.map = {
            "ALB": "Application Load Balancer",
            "AP": "API Prioritization",
            "AS": "Audience Segmentation",
            "CD": "Phased Release",
            "ER": "Edge Redirector",
            "FR": "Forward Rewrite",
            "IG": "Request Control",
            "VP": "Visitor Prioritization",
            "VWR": "Virtual Waiting Room",
        }

    async def extract_records(self):
        try:
            for v2_policy in self.client.list_v2_policies():
                yield self.parse_policy(v2_policy, 2)
        except Exception as err:
            self.logger.error(f"Failed to list v2 cloudlet policies: {err}")

        try:
            for v3_policy in self.client.list_v3_policies():
                yield self.parse_policy(v3_policy, 3)
        except Exception as err:
            self.logger.error(f"Failed to list v3 cloudlet policies: {err}")

    def parse_policy(self, policy, version):
        if version == 2:
            policy["policyType"] = self.map[policy["cloudletCode"]]
            policy["isShared"] = False
            for activation in policy["activations"]:
                if activation["network"] == "prod":
                    policy["activeProductionVersion"] = activation["policyInfo"][
                        "version"
                    ]
                if activation["network"] == "staging":
                    policy["activeStagingVersion"] = activation["policyInfo"]["version"]
            policy[
                "deeplink"
            ] = f"https://control.akamai.com/apps/cloudlets/#/policies/{policy['policyId']}/versions?gid={policy['groupId']}&shared=false"

        else:
            policy["policyType"] = self.map[policy["cloudletType"]]
            policy["isShared"] = True
            if "currentActivations" in policy.keys():
                if "production" in policy["currentActivations"].keys():
                    if "effective" in policy["currentActivations"]["production"].keys():
                        if (
                            policy["currentActivations"]["production"]["effective"]
                            is not None
                        ):
                            policy["activeProductionVersion"] = policy[
                                "currentActivations"
                            ]["production"]["effective"]["policyVersion"]
                        else:
                            policy["activeProductionVersion"] = None
                if "staging" in policy["currentActivations"].keys():
                    if "effective" in policy["currentActivations"]["staging"].keys():
                        if (
                            policy["currentActivations"]["staging"]["effective"]
                            is not None
                        ):
                            policy["activeStagingVersion"] = policy[
                                "currentActivations"
                            ]["staging"]["effective"]["policyVersion"]
                        else:
                            policy["activeStagingVersion"] = None
            policy[
                "deeplink"
            ] = f"https://control.akamai.com/apps/cloudlets/#/policies/{policy['id']}/versions?gid={policy['groupId']}&shared=true"
            policy["policyId"] = policy["id"]

        return policy
