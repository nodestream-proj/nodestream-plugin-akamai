import logging
from etwpipeline.akamai.client import AkamaiApiClient


logger = logging.getLogger(__name__)


class AkamaiNetstorageClient(AkamaiApiClient):
    def list_netstorage_groups(self):
        netstorage_groups_path = "/storage/v1/storage-groups"
        return self._get_api_from_relative_path(netstorage_groups_path)["items"]
