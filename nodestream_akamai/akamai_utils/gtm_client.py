import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiGtmClient(AkamaiApiClient):
    def list_gtm_domains(self):
        gtm_domains_path = "/config-gtm/v1/domains"
        return self._get_api_from_relative_path(gtm_domains_path)["items"]

    def get_gtm_domain(self, domain_name: str):
        gtm_domain_path = f"/config-gtm/v1/domains/{domain_name}"
        return self._get_api_from_relative_path(
            gtm_domain_path, headers={"accept": "application/vnd.config-gtm.v1.5+json"}
        )
