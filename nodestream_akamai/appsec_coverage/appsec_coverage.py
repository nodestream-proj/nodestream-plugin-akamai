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
                if "productionVersion" in config.keys():
                    config["policies"] = self.client.list_appsec_policies(
                        config["id"], config["productionVersion"]
                    )
            hostname_coverage = self.client.get_appsec_hostname_coverage()
        except Exception as err:
            self.logger.error("Failed to get appsec hostname coverage: %s", err)

        for hostname in hostname_coverage:
            # Only care if hostname is covered
            if hostname["status"] == "covered":
                # Need to find policy ID, so find first locate config from hostname entry
                covering_config = [
                    config
                    for config in configs
                    if config["id"] == hostname["configuration"]["id"]
                ][0]
                # Then iterate through policyNames and replace with dict
                for policyName in hostname["policyNames"]:
                    covering_policy = [
                        policy
                        for policy in covering_config["policies"]
                        if policy["policyName"] == policyName
                    ][0]
                    coverage_object = {
                        "hostname": hostname["hostname"],
                        "policyName": covering_policy["policyName"],
                        "policyId": covering_policy["policyId"],
                    }
                    yield coverage_object
