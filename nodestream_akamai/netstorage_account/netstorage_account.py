import logging
from hashlib import sha256

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
            self.logger.exception("Failed to list netstorage upload accounts: %s", err)
            raise err

        for account in upload_accounts:
            account["combinedKeys"] = []
            if "keys" in account:
                key_types = ["ftp", "ssh", "rsync", "aspera", "g2o"]
                for key_type in key_types:
                    if key_type in account["keys"]:
                        for key in account["keys"][key_type]:
                            http_sha256 = None
                            if key_type == "g2o":
                                http_sha256 = sha256(
                                    key["key"].encode("utf-8")
                                ).hexdigest()
                            parsed_key = {
                                "type": key_type,
                                "id": key["id"],
                                "http_sha256": http_sha256,
                                "lastModifiedBy": key["lastModifiedBy"],
                                "lastModifiedDate": key["lastModifiedDate"],
                                "isActive": key["isActive"],
                            }
                            account["combinedKeys"].append(parsed_key)

            # Remove keys element before pushing to database
            if "keys" in account:
                del account["keys"]
            yield account
