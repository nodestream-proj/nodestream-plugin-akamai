import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.cloudlets_v2_client import AkamaiCloudletsV2Client


class AkamaiRedirectExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiCloudletsV2Client(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for policy_id in self.client.cloudlet_policy_ids_er():
            try:
                policy_tree = self.client.describe_policy_id(policy_id)
                for item in self.client.get_policy_rule_set(policy_tree):
                    yield item
            except Exception:
                self.logger.error("Failed to get policy: %s", policy_id)
