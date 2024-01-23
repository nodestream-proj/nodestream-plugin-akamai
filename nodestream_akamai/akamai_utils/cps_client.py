import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiCpsClient(AkamaiApiClient):
    def list_cps_enrollments(self):
        list_enrollments_path = "/cps/v2/enrollments"
        headers = {"accept": "application/vnd.akamai.cps.enrollments.v11+json"}
        return self._get_api_from_relative_path(list_enrollments_path, headers=headers)[
            "enrollments"
        ]

    def get_cps_production_deployment(self, enrollment_id):
        cps_deployment_path = f"/cps/v2/enrollments/{enrollment_id}/deployments"
        headers = {"accept": "application/vnd.akamai.cps.deployments.v7+json"}
        return self._get_api_from_relative_path(cps_deployment_path, headers=headers)[
            "production"
        ]
