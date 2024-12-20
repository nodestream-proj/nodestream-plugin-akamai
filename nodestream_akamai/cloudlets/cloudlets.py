import logging
from enum import StrEnum

from nodestream.pipeline import Extractor

from ..akamai_utils.cloudlet_client import AkamaiCloudletClient


class PolicyType(StrEnum):
    ALB = ("ALB", "Application Load Balancer")
    AP = ("AP", "API Prioritization")
    AS = ("AS", "Audience Segmentation")
    CD = ("CD", "Phased Release")
    ER = ("ER", "Edge Redirector")
    FR = ("FR", "Forward Rewrite")
    IG = ("IG", "Request Control")
    VP = ("VP", "Visitor Prioritization")
    VWR = ("VWR", "Virtual Waiting Room")

    @property
    def title(self):
        return self._title

    def __new__(cls, key: str, title: str):
        member = str.__new__(cls, key)
        member._value_ = key
        member._title = title
        return member


deeplink_prefix = "https://control.akamai.com/apps/cloudlets/#/policies"


def v2_deeplink(v2_policy):
    return "/".join(
        [
            deeplink_prefix,
            v2_policy["policyId"],
            f"versions?gid={v2_policy['groupId']}&shared=false",
        ]
    )


def v3_deeplink(v3_policy):
    return "/".join(
        [
            deeplink_prefix,
            v3_policy["id"],
            f"versions?gid={v3_policy['groupId']}&shared=true",
        ]
    )


class AkamaiCloudletExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs):
        self.client = AkamaiCloudletClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")

    async def extract_records(self):
        try:
            for v2_policy in self.client.list_v2_policies():
                self.enhance_policy_v2(v2_policy, v2_deeplink(v2_policy))
                yield v2_policy
        except IOError as err:
            self.logger.error(f"Failed to list v2 cloudlet policies: {err}")

        try:
            for v3_policy in self.client.list_v3_policies():
                self.enhance_policy_v3(v3_policy, v3_deeplink(v3_policy))
                yield v3_policy
        except IOError as err:
            self.logger.error(f"Failed to list v3 cloudlet policies: {err}")

    def enhance_policy_v2(self, policy, deeplink):
        self.logger.debug("enhance_policy_v2(policy=%s, deeplink=%s)", policy, deeplink)
        policy_type = PolicyType[policy["cloudletCode"]]
        policy["policyType"] = policy_type.title if policy_type else None
        policy["isShared"] = False
        for activation in policy["activations"]:
            match activation["network"]:
                case "prod":
                    policy["activeProductionVersion"] = activation["policyInfo"][
                        "version"
                    ]
                case "staging":
                    policy["activeStagingVersion"] = activation["policyInfo"]["version"]
        policy["deeplink"] = deeplink
        return policy

    def enhance_policy_v3(self, policy, deeplink):
        self.logger.debug("enhance_policy_v2(policy=%s, deeplink=%s)", policy, deeplink)
        policy_type = PolicyType[policy["cloudletType"]]
        policy["policyType"] = policy_type.title if policy_type else None
        policy["isShared"] = True
        current_activations = policy.get("currentActivations", {})
        prod = current_activations.get("production", {})
        prod_effective = prod.get("effective", {})

        policy["activeProductionVersion"] = prod_effective.get("policyVersion")

        stg = current_activations.get("staging", {})
        stg_effective = stg.get("effective", {})
        policy["activeStagingVersion"] = stg_effective.get("policyVersion")

        policy["deeplink"] = deeplink
        policy["policyId"] = policy["id"]
        return policy
