import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient


def _extract_policy(covering_config, hostname, policy_name) -> dict[str, str]:
    covering_policy = next(
        policy
        for policy in covering_config["policies"]
        if policy["policyName"] == policy_name
    )
    return {
        "hostname": hostname["hostname"],
        "policy_name": covering_policy["policyName"],
        "policyId": covering_policy["policyId"],
    }


class AkamaiAppSecCoverageExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiAppSecClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            configs = self.client.list_appsec_configs()
            for config in configs:
                if "productionVersion" in config:
                    config["policies"] = self.client.list_appsec_policies(
                        config["id"], config["productionVersion"]
                    )
            hostname_coverage = self.client.get_appsec_hostname_coverage()
        except Exception as err:
            self.logger.exception("Failed to get appsec hostname coverage: %s", err)
            raise err

        for hostname in hostname_coverage:
            # Only care if hostname is covered
            if hostname.get("status") == "covered":
                # Need to find policy ID, so find first locate config from hostname entry
                covering_config = next(
                    config
                    for config in configs
                    if config["id"] == hostname["configuration"]["id"]
                )
                # Then iterate through policyNames and replace with dict
                for policy_name in hostname["policyNames"]:
                    coverage_object = _extract_policy(
                        covering_config, hostname, policy_name
                    )
                    yield coverage_object
