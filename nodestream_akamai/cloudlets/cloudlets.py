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
            self.logger.exception("Failed to list v2 cloudlet policies: %s", err)

        try:
            for v3_policy in self.client.list_v3_policies():
                yield self.parse_policy(v3_policy, 3)
        except Exception as err:
            self.logger.exception("Failed to list v3 cloudlet policies: %s", err)

    def parse_policy(self, policy, version):
        deeplink_prefix = "https://control.akamai.com/apps/cloudlets/#/policies/"
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
            policy["deeplink"] = "{prefix}{id}/versions?gid={gid}&shared=false".format(
                prefix=deeplink_prefix, id=policy["policyId"], gid=policy["groupId"]
            )

        else:
            policy["policyType"] = self.map[policy["cloudletType"]]
            policy["isShared"] = True
            if "currentActivations" in policy:
                current_activations = policy["currentActivations"]
                if (
                    "production" in current_activations
                    and "effective" in current_activations["production"]
                ):
                    if current_activations["production"]["effective"] is not None:
                        policy["activeProductionVersion"] = current_activations[
                            "production"
                        ]["effective"]["policyVersion"]
                    else:
                        policy["activeProductionVersion"] = None
                if (
                    "staging" in current_activations
                    and "effective" in current_activations["staging"]
                ):
                    if current_activations["staging"]["effective"] is not None:
                        policy["activeStagingVersion"] = current_activations["staging"][
                            "effective"
                        ]["policyVersion"]
                    else:
                        policy["activeStagingVersion"] = None
            policy["deeplink"] = "{prefix}{id}/versions?gid={gid}&shared=true".format(
                prefix=deeplink_prefix, id=policy["id"], gid=policy["groupId"]
            )
            policy["policyId"] = policy["id"]

        return policy
