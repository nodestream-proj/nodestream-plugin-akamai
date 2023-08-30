import logging

from ..akamai_utils.client import AkamaiApiClient

from nodestream.pipeline.extractors import Extractor


class AkamaiSiteShieldExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            siteshield_maps = self.client.list_siteshield_maps()
        except Exception as err:
            self.logger.error("Failed to list siteshield maps: %s", err)
            
        for map in siteshield_maps:
            yield map
