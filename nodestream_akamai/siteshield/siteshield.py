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
            self.logger.exception("Failed to list siteshield maps: %s", err)
            raise err

        for siteshield_map in siteshield_maps:
            deeplink_prefix = (
                "https://control.akamai.com/apps/siteshield-ui/#/mapRequest/"
            )
            siteshield_map[
                "deeplink"
            ] = f'{deeplink_prefix}{siteshield_map["latestTicketId"]}/status'
            yield siteshield_map
