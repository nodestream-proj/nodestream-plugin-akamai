import logging

from ..akamai_utils.netstorage_client import AkamaiNetstorageClient

from nodestream.pipeline.extractors import Extractor


class AkamaiNetstorageAccountExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiNetstorageClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            upload_accounts = self.client.list_upload_accounts()
        except Exception as err:
            self.logger.error("Failed to list netstorage upload accounts: %s", err)

        for account in upload_accounts:
            yield account
