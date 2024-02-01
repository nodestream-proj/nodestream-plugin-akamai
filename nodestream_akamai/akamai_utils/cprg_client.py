import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiCprgClient(AkamaiApiClient):
    def list_cpcodes(self):
        list_cpcodes_path = "/cprg/v1/cpcodes"
        return self._get_api_from_relative_path(list_cpcodes_path)["cpcodes"]
