import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.siteshield_client import AkamaiSiteshieldClient


class AkamaiSiteshieldExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiSiteshieldClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            siteshield_maps = self.client.list_siteshield_maps()
        except Exception as err:
            self.logger.error("Failed to list siteshield maps: %s", err)

        for map in siteshield_maps:
            deeplink_prefix = (
                "https://control.akamai.com/apps/siteshield-ui/#/mapRequest/"
            )
            map["deeplink"] = f'{deeplink_prefix}{map["latestTicketId"]}/status'
            yield map
