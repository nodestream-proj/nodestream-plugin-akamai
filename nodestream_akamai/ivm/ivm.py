import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.contract_client import AkamaiContractClient
from ..akamai_utils.ivm_client import AkamaiIvmClient


class AkamaiIvmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiIvmClient(**akamai_client_kwargs)
        self.contract_client = AkamaiContractClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        # List contracts
        try:
            contracts = self.contract_client.list_contracts()
        except Exception:
            self.logger.error("Failed to list contracts")
            self.logger.error(err)

        # Iterate through contracts to find IVM-enabled
        ivm_contracts = []
        for contract in contracts:
            products = self.contract_client.list_products_per_contract(
                contract_id=contract
            )

            ivm_products = [
                "Image and Video Manager - Image Optimization",
                "Image Manager",
            ]
            ivm_found = [
                product
                for product in products
                if product["marketingProductName"] in ivm_products
            ]
            if len(ivm_found) > 0:
                ivm_contracts.append(contract)

        try:
            for contract in ivm_contracts:
                for policy_set in self.client.list_policy_sets(contract=contract):
                    if "user" not in policy_set.keys():
                        self.logger.warning(
                            f"""Policy set '{policy_set["id"]}' does not appear to be valid and will be skipped. Please report this to Akamai support"""
                        )
                        continue
                    try:
                        for policy in self.client.list_policies(policy_set["id"])[
                            "items"
                        ]:
                            policy["policySetId"] = policy_set["id"]
                            policy["uniqueId"] = policy_set["id"] + "/" + policy["id"]
                            yield policy
                    except Exception as err:
                        self.logger.error(
                            "Failed to list policies of policy set: %s",
                            policy_set["id"],
                        )
                        self.logger.error(err)
        except Exception as err:
            self.logger.error("Failed to list IVM policy sets")
            self.logger.error(err)
