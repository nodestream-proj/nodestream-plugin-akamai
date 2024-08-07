import logging
from ipaddress import IPv4Address, ip_address

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.edns_client import AkamaiEdnsClient


class AkamaiEdnsExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdnsClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_address_format(self, address):
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
        supported_record_types = ["A", "AAAA", "CNAME", "NS", "CAA"]
        for zone in self.client.list_zones():
            try:
                zone["recordsets"] = self.client.list_recordsets(zone["zone"])
            except Exception:
                self.logger.error(
                    f"Failed to list record sets for zone: {zone['zone']}"
                )
            for i in range(len(zone["recordsets"])):
                if zone["recordsets"][i]["type"] in supported_record_types:
                    zone["recordsets"][i]["key"] = (
                        zone["recordsets"][i]["name"]
                        + "/"
                        + zone["recordsets"][i]["type"]
                    )
                    zone["recordsets"][i]["zone"] = zone["zone"]
                    if zone["recordsets"][i]["type"] == "A":
                        zone["recordsets"][i]["Cidripv4"] = zone["recordsets"][i][
                            "rdata"
                        ]
                    if zone["recordsets"][i]["type"] == "AAAA":
                        zone["recordsets"][i]["Cidripv6"] = zone["recordsets"][i][
                            "rdata"
                        ]
                    if zone["recordsets"][i]["type"] == "CNAME":
                        zone["recordsets"][i]["Endpoint"] = zone["recordsets"][i][
                            "rdata"
                        ]
                    if zone["recordsets"][i]["type"] == "NS":
                        zone["recordsets"][i]["Cidripv4"] = []
                        zone["recordsets"][i]["Cidripv6"] = []
                        zone["recordsets"][i]["Endpoint"] = []
                        for record in zone["recordsets"][i]["rdata"]:
                            address_format = self.get_address_format(record)
                            if address_format == "ipv4":
                                zone["recordsets"][i]["Cidripv4"].append(record)
                            elif address_format == "ipv6":
                                zone["recordsets"][i]["Cidripv6"].append(record)
                            elif address_format == "endpoint":
                                zone["recordsets"][i]["Endpoint"].append(record)
            yield zone
