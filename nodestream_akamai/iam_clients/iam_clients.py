import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.iam_client import AkamaiIamClient


class AkamaiIamClientExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiIamClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            clients = self.client.list_api_clients()
        except Exception as err:
            self.logger.exception("Failed to list api clients: %s", err)
            raise err

        for client in clients:
            client["authorizedUsersList"] = ",".join(client["authorizedUsers"])
            client[
                "deeplink"
            ] = "https://control.akamai.com/apps/identity-management/#/tabs/users/list/api-client/{id}/details".format(
                id=client["clientId"]
            )
            if client["activeCredentialCount"] > 0:
                try:
                    credentials = self.client.list_api_credentials(client["clientId"])
                    client["credentials"] = [
                        credential
                        for credential in credentials
                        if credential["status"] == "ACTIVE"
                    ]
                except Exception as err:
                    self.logger.exception(
                        "Failed to list credentials for client '%s': %s",
                        client["clientId"],
                        err,
                    )

            yield client
