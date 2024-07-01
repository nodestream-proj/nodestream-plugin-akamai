import json
import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.edns_client import AkamaiEdnsClient


class AkamaiEdnsExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdnsClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for zone in self.client.list_zones():
            try:
                zone["recordsets"] = self.client.list_recordsets(zone["zone"])
            except Exception:
                self.logger.error(
                    f"Failed to list record sets for zone: {zone['zone']}"
                )
            for i in range(len(zone["recordsets"])):
                zone["recordsets"][i]["zone"] = zone["zone"]
                if zone["recordsets"][i]["type"] == "A":
                    zone["recordsets"][i]["Cidripv4"] = zone["recordsets"][i]["rdata"]
                if zone["recordsets"][i]["type"] == "AAAA":
                    zone["recordsets"][i]["Cidripv6"] = zone["recordsets"][i]["rdata"]
                if zone["recordsets"][i]["type"] == "CNAME":
                    zone["recordsets"][i]["Endpoint"] = zone["recordsets"][i]["rdata"]
            yield zone
