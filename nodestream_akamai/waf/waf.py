import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient

# Fallback names for attack groups missing from the export's rulesets.
AG_MAP = {
    "POLICY": "Web Policy Violation",
    "WAT": "Web Attack Tool",
    "TOOL": "Web Attack Tool",
    "PROTOCOL": "Web Protocol Attack",
    "SQL": "SQL Injection",
    "XSS": "Cross Site Scripting",
    "CMD": "Command Injection",
    "CMDI": "Command Injection",
    "LFI": "Local File Inclusion",
    "RFI": "Remote File Inclusion",
    "PLATFORM": "Web Platform Attack",
    "OUTBOUND": "Total Outbound",
}


def _attack_group_names(export) -> dict:
    """Map attack group code to its name, from the export's rulesets."""
    names = {}
    for ruleset in export.get("rulesets", []):
        for group in ruleset.get("attackGroups", []):
            names.setdefault(group["group"], group.get("groupName"))
    return names


def _rate_policy(config_id, rate_policy) -> dict:
    """Config-level rate policy, written as an AkamaiRatePolicy node."""
    return {
        "configId": config_id,
        "ratePolicyId": rate_policy["id"],
        "name": rate_policy.get("name"),
        "type": rate_policy.get("type"),
        "averageThreshold": rate_policy.get("averageThreshold"),
        "burstThreshold": rate_policy.get("burstThreshold"),
        "burstWindow": rate_policy.get("burstWindow"),
        "matchType": rate_policy.get("matchType"),
        "used": rate_policy.get("used"),
    }


def _reputation_profile(config_id, profile) -> dict:
    """Config-level client reputation profile, written as an
    AkamaiReputationProfile node."""
    return {
        "configId": config_id,
        "reputationProfileId": profile["id"],
        "name": profile.get("name"),
        "context": profile.get("context"),
        "contextReadable": profile.get("contextReadable"),
        "enabled": profile.get("enabled"),
        "threshold": profile.get("threshold"),
        "sharedIpHandling": profile.get("sharedIpHandling"),
    }


def _policy_record(config_id, policy, group_names) -> dict:
    """One record per security policy.

    Feeds the HAS_RATE_POLICY, HAS_ATTACK_GROUP and HAS_REPUTATION_PROFILE
    links of an AkamaiWafPolicy node (matched by policy_id; the node itself
    comes from the config record). Each action is set per (security policy,
    X) pair, so it lives on the relationship. This record has no top-level
    configId, so the AkamaiWafConfig pass in waf.yaml skips it (null source
    key).

    The export omits reputation profiles whose action is "none", so a
    profile with no HAS_REPUTATION_PROFILE relationship is off in that policy.
    """
    waf = policy.get("webApplicationFirewall", {})
    reputation = policy.get("clientReputation", {})
    return {
        "policyId": policy["id"],
        "ratePolicyActions": [
            {
                "configId": config_id,
                "ratePolicyId": action["id"],
                "ipv4Action": action.get("ipv4Action"),
                "ipv6Action": action.get("ipv6Action"),
            }
            for action in policy.get("ratePolicyActions", [])
        ],
        "attackGroupActions": [
            {
                "group": action["group"],
                "groupName": group_names.get(action["group"])
                or AG_MAP.get(action["group"]),
                "action": action.get("action"),
            }
            for action in waf.get("attackGroupActions", [])
        ],
        "reputationProfileActions": [
            {
                "configId": config_id,
                "reputationProfileId": action["id"],
                "action": action.get("action"),
            }
            for action in reputation.get("reputationProfileActions", [])
        ],
    }


def _has_relationships(policy_record) -> bool:
    return any(
        policy_record[key]
        for key in (
            "ratePolicyActions",
            "attackGroupActions",
            "reputationProfileActions",
        )
    )


DEEPLINK_PREFIX = "https://control.akamai.com/apps/security-config/#/next/configs/"


def _waf_policies(export) -> list:
    """Security policies with a webApplicationFirewall block.

    A policy without one has its WAF turned off, so it protects nothing and
    is left out of the graph entirely (no node, no relationships).
    """
    return [
        policy
        for policy in export["securityPolicies"]
        if "webApplicationFirewall" in policy
    ]


def _config_record(config, export) -> dict:
    """One record per config.

    Feeds the AkamaiWafConfig node, its AkamaiWafPolicy nodes (name, deeplink,
    control flags) and the config's AkamaiRatePolicy and
    AkamaiReputationProfile nodes.
    """
    config_deeplink = (
        f'{DEEPLINK_PREFIX}{config["id"]}/versions/{config["productionVersion"]}'
    )
    policies = []
    for policy in _waf_policies(export):
        security_controls = policy.get("securityControls", {})
        policies.append(
            {
                "policyId": policy["id"],
                "policyName": policy["name"],
                "rateControlsEnabled": security_controls.get("applyRateControls"),
                "botManagerEnabled": security_controls.get("applyBotmanControls"),
                "reputationControlsEnabled": security_controls.get(
                    "applyReputationControls"
                ),
                "deeplink": f'{config_deeplink}/policies/{policy["id"]}',
            }
        )
    return {
        "configId": config["id"],
        "configName": config["name"],
        "productionVersion": config["productionVersion"],
        "policies": policies,
        "ratePolicies": [
            _rate_policy(config["id"], rate_policy)
            for rate_policy in export.get("ratePolicies", [])
        ],
        "reputationProfiles": [
            _reputation_profile(config["id"], profile)
            for profile in export.get("reputationProfiles", [])
        ],
        "deeplink": config_deeplink,
    }


class AkamaiWafExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiAppSecClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for config in self.client.list_appsec_configs():
            try:
                if "productionVersion" in config:
                    export = self.client.export_appsec_config(
                        config_id=config["id"],
                        config_version=config["productionVersion"],
                    )
                    group_names = _attack_group_names(export)
                    # Build every record before yielding, so a config that
                    # fails part-way yields nothing.
                    config_record = _config_record(config, export)
                    policy_records = [
                        record
                        for record in (
                            _policy_record(config["id"], policy, group_names)
                            for policy in _waf_policies(export)
                        )
                        if _has_relationships(record)
                    ]
                    yield config_record
                    for policy_record in policy_records:
                        yield policy_record
                else:
                    self.logger.warning(
                        "No production version exists for config %s.", config["name"]
                    )
            except Exception as err:
                self.logger.exception(
                    "Failed to export appsec configuration %s: %s",
                    config["name"],
                    err,
                )
