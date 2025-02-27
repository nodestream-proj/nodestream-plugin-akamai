import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient


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
            if hostname["status"] == "covered":
                # Need to find policy ID, so find first locate config from hostname entry
                covering_config = next(
                    config
                    for config in configs
                    if config["id"] == hostname["configuration"]["id"]
                )
                # Then iterate through policyNames and replace with dict
                for policy_name in hostname["policyNames"]:
                    covering_policy = next(
                        policy
                        for policy in covering_config["policies"]
                        if policy["policy_name"] == policy_name
                    )
                    coverage_object = {
                        "hostname": hostname["hostname"],
                        "policy_name": covering_policy["policy_name"],
                        "policyId": covering_policy["policyId"],
                    }
                    yield coverage_object
