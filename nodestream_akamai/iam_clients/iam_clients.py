import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.iam_client import AkamaiIamClient


class AkamaiIamClientExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiIamClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            for client in self.client.list_api_clients():
                client["authorizedUsersList"] = ",".join(client["authorizedUsers"])
                client[
                    "deeplink"
                ] = f'https://control.akamai.com/apps/identity-management/#/tabs/users/list/api-client/{client["clientId"]}/details'
                yield client
        except Exception as err:
            self.logger.error("Failed to list api clients: %s", err)
