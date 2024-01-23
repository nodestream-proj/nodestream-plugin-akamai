import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.edgehostnames_client import AkamaiEdgeHostnamesClient


class AkamaiEhnExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdgeHostnamesClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            for edge_hostname in self.client.list_edge_hostnames():
                edge_hostname["edgeHostname"] = (
                    edge_hostname["recordName"] + "." + edge_hostname["dnsZone"]
                )
                yield edge_hostname
        except Exception as err:
            self.logger.error("Failed to list edge hostnames: %s", err)
