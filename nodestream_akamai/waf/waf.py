import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient


class AkamaiWafExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiAppSecClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        ag_map = {
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

        for config in self.client.list_appsec_configs():
            try:
                if "productionVersion" in config.keys():
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
                        "policies": [],
                        "deeplink": f'{deeplink_prefix}{config["id"]}/versions/{config["productionVersion"]}',
                    }
                    # Iterate through policies and add custom dict to output
                    for policy in export["securityPolicies"]:
                        output_policy = {
                            "policyId": policy["id"],
                            "policyName": policy["name"],
                            "attackGroupActions": [],
                        }
                        if "webApplicationFirewall" in policy.keys():
                            for action in policy["webApplicationFirewall"][
                                "attackGroupActions"
                            ]:
                                output_policy["attackGroupActions"].append(
                                    {
                                        "group": action["group"],
                                        "groupName": ag_map[action["group"]],
                                        "action": action["action"],
                                    }
                                )
                            output_config["policies"].append(output_policy)

                    yield output_config
                else:
                    self.logger.warning(
                        f"No production version exists for config {config['name']}"
                    )
            except Exception as err:
                self.logger.error(
                    f"Failed to export appsec configuration {config['name']}: {err}"
                )
