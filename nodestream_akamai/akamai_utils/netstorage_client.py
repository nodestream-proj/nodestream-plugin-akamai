import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiNetstorageClient(AkamaiApiClient):
    def list_netstorage_groups(self):
        return self._get_api_from_relative_path("/storage/v1/storage-groups")["items"]

    def list_upload_accounts(self):
        return self._get_api_from_relative_path("/storage/v1/upload-accounts")["items"]
