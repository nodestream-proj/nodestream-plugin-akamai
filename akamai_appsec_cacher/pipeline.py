import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiAppSecExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        try:
            hostname_coverage = self.client.get_appsec_hostname_coverage()
        except Exception as err:
            self.logger.error("Failed to get appsec hostname coverage: %s", err)
            
        for hostname in hostname_coverage:
            yield hostname

def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_appsec_cacher/pipeline.yaml")
