import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.appsec_client import AkamaiAppSecClient


class AkamaiAPIDiscoveryExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiAppSecClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            discovered_apis = self.client.list_discovered_apis()
        except Exception as err:
            self.logger.error("Failed to list discovered apis: %s", err)

        for api in discovered_apis:
            try:
                api_detail = self.client.get_discovered_api(
                    hostname=api["encodedHost"], basePath=api["encodedBasePath"]
                )
                api_detail["id"] = f'{api_detail["host"]}{api_detail["basePath"]}'
                yield api_detail
            except Exception as err:
                self.logger.error(
                    "Failed to retrieve api '%s - %s': %s",
                    api["encodedHost"],
                    api["encodedBasePath"],
                    err,
                )
