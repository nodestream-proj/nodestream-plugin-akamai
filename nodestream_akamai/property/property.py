import logging

from akamai_utils.client import AkamaiApiClient

from nodestream.pipeline.extractors import Extractor


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

        production_active_properties = [property for property in properties if property['productionVersion'] is not None]
        for property in production_active_properties:
            try:
                print(str(property))
                yield self.client.describe_property_by_dict(property).as_eventbus_json()
            except Exception as err:
                self.logger.error("Failed to get property: {p}, {e}".format(p = property['propertyId'], e = err))