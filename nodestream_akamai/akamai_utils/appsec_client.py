import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiAppSecClient(AkamaiApiClient):
    def get(self, path):
        return self._get_api_from_relative_path(f"/appsec/v1{path}")

    def get_configs(self, path=""):
        return self.get(f"/configs{path}")

    def get_api_discovery(self, path=""):
        return self.get(f"/api-discovery{path}")

    def get_appsec_hostname_coverage(self):
        return self.get("/hostname-coverage")["hostnameCoverage"]

    def list_appsec_configs(self):
        return self.get_configs()["configurations"]

    def list_appsec_policies(self, config_id, version):
        response = self.get_configs(
            f"/{config_id}/versions/{version}/security-policies"
        )
        return response["policies"]

    def export_appsec_config(self, config_id: int, config_version: int):
        return self.get(f"/export/configs/{config_id}/versions/{config_version}")

    def list_discovered_apis(self):
        return self.get_api_discovery()["apis"]

    def get_discovered_api(self, hostname, base_path):
        return self.get_api_discovery(f"/host/{hostname}/basepath/{base_path}")
