import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiPropertyExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.error("Failed to list properties: %s", err)
            return

        for property in properties:
            try:
                yield self.client.describe_property_by_dict(property).as_eventbus_json()
            except Exception as err:
                self.logger.error("Failed to get property: {p}, {e}".format(p = property['propertyId'], e = err))


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_property_cacher/pipeline.yaml")
