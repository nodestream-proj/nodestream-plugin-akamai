import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.ivm_client import AkamaiIvmClient


class AkamaiIvmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiIvmClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            for policy_set in self.client.list_policy_sets():
                try:
                    for policy in self.client.list_policies(policy_set["id"])["items"]:
                        policy["policySetId"] = policy_set["id"]
                        policy["uniqueId"] = policy_set["id"] + "/" + policy["id"]
                        yield policy
                except Exception as err:
                    self.logger.error(
                        "Failed to list policies of policy set: %s", policy_set["id"]
                    )
                    self.logger.error(err)
        except Exception:
            self.logger.error("Failed to list IVM policy sets")
