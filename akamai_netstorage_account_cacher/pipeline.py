import logging

from etwpipeline.akamai.netstorage_client import AkamaiNetstorageClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiNetstorageAccountExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiNetstorageClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        try:
            upload_accounts = self.client.list_upload_accounts()
        except Exception as err:
            self.logger.error("Failed to list netstorage upload accounts: %s", err)

        for account in upload_accounts:
            yield account


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_netstorage_account_cacher/pipeline.yaml")
