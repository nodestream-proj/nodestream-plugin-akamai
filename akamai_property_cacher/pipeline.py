import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiPropertyExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        for group_id, contract_id in self.client.contracts_by_group():
            for property_id in self.client.property_ids_for_contract_group(
                group_id, contract_id
            ):
                try:
                    yield self.client.describe_property_by_id(property_id).as_eventbus_json()
                except Exception:
                    self.logger.error("Failed to get property: %s", property_id)


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_property_cacher/pipeline.yaml")
