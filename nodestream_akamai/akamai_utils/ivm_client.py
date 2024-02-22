import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiIvmClient(AkamaiApiClient):
    def list_policy_sets(self, contract=None):
        ivm_policy_sets_path = "/imaging/v2/policysets"
        if contract is not None:
            headers = {"Contract": contract}
        return self._get_api_from_relative_path(ivm_policy_sets_path, headers=headers)

    def list_policies(self, policy_set_id: str, contract=None):
        ivm_policies_path = f"/imaging/v2/network/production/policies"
        headers = {"Policy-Set": policy_set_id}
        if contract is not None:
            headers["Contract"] = contract
        return self._get_api_from_relative_path(ivm_policies_path, headers=headers)
