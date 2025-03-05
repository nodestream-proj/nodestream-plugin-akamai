import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.property_client import AkamaiPropertyClient


class AkamaiPropertyExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiPropertyClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        self.logger.debug("extracting records")
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.exception("Failed to list properties: %s", err)
            raise err

        for prop in properties:
            if prop.get("productionVersion") is None:
                continue
            self.logger.info(
                "extracting property %s (id=%s)",
                prop.get("propertyName"),
                prop.get("propertyId"),
            )
            try:
                described_property = self.client.describe_property_by_dict(prop)
                yield described_property.as_eventbus_json()
            except Exception:
                self.logger.exception(
                    "Failed to get property %s (id=%s)",
                    prop["propertyName"],
                    prop["propertyId"],
                )
