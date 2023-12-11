import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiSiteshieldClient(AkamaiApiClient):
    def list_siteshield_maps(self):
        siteshield_maps_path = "/siteshield/v1/maps"
        return self._get_api_from_relative_path(siteshield_maps_path)["siteShieldMaps"]
