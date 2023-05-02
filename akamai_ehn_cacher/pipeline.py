import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiEHNExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
            try:
                for edge_hostname in self.client.list_edge_hostnames():
                    yield edge_hostname
            except Exception as err:
                self.logger.error("Failed to list edge hostnames: %s", err)

def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_ehn_cacher/pipeline.yaml")
