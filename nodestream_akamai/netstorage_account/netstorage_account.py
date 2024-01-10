import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.netstorage_client import AkamaiNetstorageClient


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
            account["combinedKeys"] = []
            if "keys" in account.keys():
                key_types = ["ftp", "ssh", "rsync", "aspera", "g2o"]
                for key_type in key_types:
                    if key_type in account["keys"].keys():
                        for key in account["keys"][key_type]:
                            parsed_key = {
                                "type": key_type,
                                "id": key["id"],
                                "lastModifiedBy": key["lastModifiedBy"],
                                "lastModifiedDate": key["lastModifiedDate"],
                            }
                            account["combinedKeys"].append(parsed_key)

            # Remove keys element before pushing to database
            if "keys" in account.keys():
                del account["keys"]
            yield account
