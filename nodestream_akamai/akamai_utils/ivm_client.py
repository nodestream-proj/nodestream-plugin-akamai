import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiIvmClient(AkamaiApiClient):
    def list_policy_sets(self):
        ivm_policy_sets_path = "/imaging/v2/policysets"
        return self._get_api_from_relative_path(ivm_policy_sets_path)

    def list_policies(self, policy_set_id: str):
        ivm_policies_path = f"/imaging/v2/network/production/policies"
        return self._get_api_from_relative_path(
            ivm_policies_path, headers={"Policy-Set": f"{policy_set_id}"}
        )
