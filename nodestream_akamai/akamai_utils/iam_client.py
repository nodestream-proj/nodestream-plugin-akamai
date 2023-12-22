import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiIAMClient(AkamaiApiClient):
    def list_users(self):
        list_users_path = "/identity-management/v3/user-admin/ui-identities"
        return self._get_api_from_relative_path(list_users_path)

    def list_api_clients(self):
        list_users_path = "/identity-management/v3/api-clients"
        return self._get_api_from_relative_path(list_users_path)
