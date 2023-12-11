import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiEdgeHostnamesClient(AkamaiApiClient):
    def list_edge_hostnames(self):
        list_ehn_path = "/hapi/v1/edge-hostnames"
        return self._get_api_from_relative_path(list_ehn_path)["edgeHostnames"]
