import logging
from enum import StrEnum

from nodestream.pipeline import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient

_WEB_ATTACK_TOOL = "Web Attack Tool"
_COMMAND_INJECTION = "Command Injection"


class ActionGroup(StrEnum):
    POLICY = ("POLICY", "Web Policy Violation")
    WAT = ("WAT", _WEB_ATTACK_TOOL)
    TOOL = ("TOOL", _WEB_ATTACK_TOOL)
    PROTOCOL = ("PROTOCOL", "Web Protocol Attack")
    SQL = ("SQL", "SQL Injection")
    XSS = ("XSS", "Cross Site Scripting")
    CMD = ("CMD", _COMMAND_INJECTION)
    CMDI = ("CMDI", _COMMAND_INJECTION)
    LFI = ("LFI", "Local File Inclusion")
    RFI = ("RFI", "Remote File Inclusion")
    PLATFORM = ("PLATFORM", "Web Platform Attack")
    OUTBOUND = ("OUTBOUND", "Total Outbound")

    @property
    def title(self):
        return self._title

    def __new__(cls, key: str, title: str):
        member = str.__new__(cls, key)
        member._value_ = key
        member._title = title
        return member


class AkamaiWafExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiAppSecClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")

    async def extract_records(self):
        for config in self.client.list_appsec_configs():
            try:
                if "productionVersion" in config:
                    export = self.client.export_appsec_config(
                        config_id=config["id"],
                        config_version=config["productionVersion"],
                    )
                    deeplink_prefix = "https://control.akamai.com/apps/security-config/#/next/configs/"
                    # Construct output dict
                    output_config = {
                        "configId": config["id"],
                        "configName": config["name"],
                        "productionVersion": config["productionVersion"],
                        "policies": [
                            self.extract_policy(policy)
                            for policy in export["securityPolicies"]
                        ],
                        "deeplink": f'{deeplink_prefix}{config["id"]}/versions/{config["productionVersion"]}',
                    }
                    # Iterate through policies and add custom dict to output

                    yield output_config
                else:
                    self.logger.warning(
                        f"No production version exists for config {config['name']}"
                    )
            except Exception as err:
                self.logger.error(
                    f"Failed to export appsec configuration {config['name']}: {err}"
                )

    def extract_attack_group_action(self, action):
        self.logger.debug("extracting attack group action")
        action_group = ActionGroup[action["group"]]

        return {
            "group": action["group"],
            "groupName": action_group.title if action_group else None,
            "action": action["action"],
        }

    def extract_policy(self, policy):
        self.logger.debug("extracting policy")
        waf = policy.get("webApplicationFirewall", {})
        attack_group_actions = waf.get("attackGroupActions", [])
        return {
            "policyId": policy["id"],
            "policyName": policy["name"],
            "attackGroupActions": [
                self.extract_attack_group_action(action)
                for action in attack_group_actions
            ],
        }
