import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiEdnsClient(AkamaiApiClient):
    def list_zones(self):
        path = "/config-dns/v2/zones?showAll=true"
        return self._get_api_from_relative_path(path)["zones"]

    def list_recordsets(self, zone):
        path = f"/config-dns/v2/zones/{zone}/recordsets?showAll=true"
        return self._get_api_from_relative_path(path)["recordsets"]
