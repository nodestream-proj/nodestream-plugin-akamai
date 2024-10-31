import logging
from ipaddress import IPv4Address, ip_address

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.gtm_client import AkamaiGtmClient


class AkamaiGtmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiGtmClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        # We only extract linked ipv4, ipv6 and endpoint types from these property types
        self.PARSED_PROPERTY_TYPES = [
            "weighted-round-robin",
            "weighted-hashed",
            "weighted-round-robin-load-feedback",
            "ranked-failover",
            "failover",
            "performance",
        ]
        self.DEEPLINK_PREFIX = "https://control.akamai.com/apps/gtm/#/domains/"
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
        for domain in self.client.list_gtm_domains():
            try:
                raw_domain = self.client.get_gtm_domain(domain["name"])
            except Exception as err:
                self.logger.error(f"Failed to get gtm domain: {domain['name']}")
                self.logger.error(err)

            deeplink = f'{self.DEEPLINK_PREFIX}{domain["name"]}/properties/list'
            properties = []
            for property in raw_domain["properties"]:
                fqdn = property["name"] + "." + raw_domain["name"]
                out_property = {
                    "fqdn": fqdn,
                    "type": property["type"],
                    "name": property["name"],
                    "Endpoint": [],
                    "Cidripv4": [],
                    "Cidripv6": [],
                }

                if property["type"] in self.PARSED_PROPERTY_TYPES:
                    for traffic_target in property["trafficTargets"]:
                        if len(traffic_target["servers"]) > 0:
                            for server in traffic_target["servers"]:
                                address_format = self._get_address_format(server)
                                node_type = self.ADDRESS_FORMAT_TO_NODE_TYPE.get(
                                    address_format
                                )
                                if node_type:
                                    out_property[node_type].append(server)
                        if traffic_target["handoutCName"]:
                            out_property["Endpoint"].append(
                                traffic_target["handoutCName"]
                            )
                for rrset in property["staticRRSets"]:
                    for record in rrset["rdata"]:
                        address_format = self._get_address_format(record)
                        node_type = self.ADDRESS_FORMAT_TO_NODE_TYPE.get(address_format)
                        if node_type:
                            out_property[node_type].append(record)

                properties.append(out_property)
            parsed_domain = {
                "name": raw_domain["name"],
                "properties": properties,
                "type": raw_domain["type"],
                "loadImbalancePercentage": raw_domain["loadImbalancePercentage"],
                "loadFeedback": raw_domain["loadFeedback"],
                "cnameCoalescingEnabled": raw_domain["cnameCoalescingEnabled"],
                "deeplink": deeplink,
            }
            yield parsed_domain
