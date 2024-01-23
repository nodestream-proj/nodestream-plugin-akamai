import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiEdgeworkersClient(AkamaiApiClient):
    def list_edgeworkers(self):
        list_edgeworkers_path = "/edgeworkers/v1/ids"
        return self._get_api_from_relative_path(list_edgeworkers_path)["edgeWorkerIds"]

    def get_production_version(self, edgeworker_id):
        get_production_version_path = f"/edgeworkers/v1/ids/{edgeworker_id}/activations?network=PRODUCTION&activeOnNetwork=true"
        activations = self._get_api_from_relative_path(get_production_version_path)[
            "activations"
        ]
        if len(activations) > 0:
            return activations[0]
        else:
            return None
