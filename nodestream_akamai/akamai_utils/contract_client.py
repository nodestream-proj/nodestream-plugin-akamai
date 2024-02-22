import logging

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiContractClient(AkamaiApiClient):
    def list_contracts(self):
        contracts_path = "/contract-api/v1/contracts/identifiers"
        return self._get_api_from_relative_path(contracts_path)

    def list_products_per_contract(self, contract_id):
        product_path = f"/contract-api/v1/contracts/{contract_id}/products/summaries"
        return self._get_api_from_relative_path(product_path)["products"][
            "marketing-products"
        ]
