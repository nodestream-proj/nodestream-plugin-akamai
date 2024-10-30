import json
import logging
from ipaddress import IPv4Address, ip_address

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.edns_client import AkamaiEdnsClient


class AkamaiEdnsExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdnsClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.SUPPORTED_RECORD_TYPES = ["A", "AAAA", "CNAME", "NS", "CAA"]
        self.ADDRESS_FORMAT_TO_NODE_TYPE = {
            "ipv4": "Cidripv4",
            "ipv6": "Cidripv6",
            "endpoint": "Endpoint",
        }

    def _get_address_format(self, address):
        try:
            if type(ip_address(address)) is IPv4Address:
                return "ipv4"
            else:
                return "ipv6"
        except ValueError:
            if " " in address:
                return "Invalid"
            else:
                return "endpoint"

    async def extract_records(self):
        for zone in self.client.list_zones():
            try:
                zone["recordsets"] = self.client.list_recordsets(zone["zone"])
            except Exception:
                self.logger.error(
                    f"Failed to list record sets for zone: {zone['zone']}"
                )
            for i in range(len(zone["recordsets"])):
                if zone["recordsets"][i]["type"] in self.SUPPORTED_RECORD_TYPES:
                    for (
                        supported_node_type
                    ) in self.ADDRESS_FORMAT_TO_NODE_TYPE.values():
                        zone["recordsets"][i][supported_node_type] = []
                    zone["recordsets"][i]["key"] = (
                        zone["recordsets"][i]["name"]
                        + "/"
                        + zone["recordsets"][i]["type"]
                    )
                    zone["recordsets"][i]["zone"] = zone["zone"]
                    for record in zone["recordsets"][i]["rdata"]:
                        address_format = self._get_address_format(record)
                        node_type = self.ADDRESS_FORMAT_TO_NODE_TYPE.get(address_format)
                        if node_type:
                            zone["recordsets"][i][node_type].append(record)
            yield zone
