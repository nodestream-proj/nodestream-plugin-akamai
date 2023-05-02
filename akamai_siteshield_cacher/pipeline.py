import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiSiteShieldExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        try:
            siteshield_maps = self.client.list_siteshield_maps()
        except Exception as err:
            self.logger.error("Failed to list siteshield maps: %s", err)
            
        for map in siteshield_maps:
            yield map

def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_siteshield_cacher/pipeline.yaml")
