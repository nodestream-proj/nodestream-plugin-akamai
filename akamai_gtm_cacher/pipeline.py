import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiGTMExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        for domain in self.client.list_gtm_domains():
            try:
                yield self.client.get_gtm_domain(domain['name'])
            except Exception:
                self.logger.error("Failed to get gtm domain: %s", domain['name'])


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_gtm_cacher/pipeline.yaml")
