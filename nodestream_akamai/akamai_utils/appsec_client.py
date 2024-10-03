import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiAppSecClient(AkamaiApiClient):
    def get_appsec_hostname_coverage(self):
        hostname_coverage_path = "/appsec/v1/hostname-coverage"
        return self._get_api_from_relative_path(hostname_coverage_path)[
            "hostnameCoverage"
        ]

    def list_appsec_configs(self):
        appsec_configs_path = "/appsec/v1/configs"
        return self._get_api_from_relative_path(appsec_configs_path)["configurations"]

    def list_appsec_policies(self, configId, version):
        appsec_configs_path = "/appsec/v1/configs/{configId}/versions/{versionNumber}/security-policies".format(
            configId=configId, versionNumber=version
        )
        return self._get_api_from_relative_path(appsec_configs_path)["policies"]

    def export_appsec_config(self, config_id: int, config_version: int):
        export_config_path = (
            f"/appsec/v1/export/configs/{config_id}/versions/{config_version}"
        )
        return self._get_api_from_relative_path(export_config_path)

    def list_discovered_apis(self):
        request_path = "/appsec/v1/api-discovery"
        return self._get_api_from_relative_path(request_path)["apis"]

    def get_discovered_api(self, hostname, basePath):
        request_path = f"/appsec/v1/api-discovery/host/{hostname}/basepath/{basePath}"
        return self._get_api_from_relative_path(request_path)
