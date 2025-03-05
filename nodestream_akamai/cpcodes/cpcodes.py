import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.cprg_client import AkamaiCprgClient


class AkamaiCpCodesExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiCprgClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            for cpcode in self.client.list_cpcodes():
                products = [p["productName"] for p in cpcode["products"]]
                cpcode["productList"] = ",".join(products)
                deeplink_prefix = (
                    "https://control.akamai.com/apps/cpcontract/#/cpcodes/"
                )
                cpcode["deeplink"] = f'{deeplink_prefix}{cpcode["cpcodeId"]}/view'
                yield cpcode
        except Exception as err:
            self.logger.exception("Failed to list CP Codes: %s", err)
            raise err
