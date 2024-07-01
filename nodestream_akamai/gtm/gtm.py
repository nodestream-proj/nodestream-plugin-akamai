import logging
from ipaddress import IPv4Address, IPv6Address, ip_address

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.gtm_client import AkamaiGtmClient


class AkamaiGtmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiGtmClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_target_type(self, target) -> str:
        parsed_target = "endpoint"
        try:
            parsed_ip = ip_address(target)
            if type(parsed_ip) is IPv4Address:
                parsed_target = "ipv4"
            elif type(parsed_ip) is IPv6Address:
                parsed_target = "ipv6"
        except ValueError:
            pass
        return parsed_target

    async def extract_records(self):
        # We only extract linked ipv4, ipv6 and endpoint types from these property types
        parsed_types = [
            "weighted-round-robin",
            "weighted-hashed",
            "weighted-round-robin-load-feedback",
            "ranked-failover",
            "failover",
        ]
        for domain in self.client.list_gtm_domains():
            try:
                raw_domain = self.client.get_gtm_domain(domain["name"])
            except Exception as err:
                self.logger.error(f"Failed to get gtm domain: {domain['name']}")
                self.logger.error(err)
            deeplink_prefix = "https://control.akamai.com/apps/gtm/#/domains/"
            deeplink = f'{deeplink_prefix}{domain["name"]}/properties/list'
            properties = []
            for property in raw_domain["properties"]:
                fqdn = property["name"] + "." + raw_domain["name"]
                endpoints = []
                Cidripv4 = []
                Cidripv6 = []
                if property["type"] in parsed_types:
                    for traffic_target in property["trafficTargets"]:
                        if len(traffic_target["servers"]) > 0:
                            for server in traffic_target["servers"]:
                                parsed_server = self.get_target_type(server)
                                if parsed_server == "ipv4":
                                    Cidripv4.append(server)
                                elif parsed_server == "ipv6":
                                    Cidripv6.append(server)
                                else:
                                    endpoints.append(server)
                        if traffic_target["handoutCName"]:
                            endpoints.append(traffic_target["handoutCName"])
                for record in property["staticRRSets"]:
                    if record["type"] == "A":
                        Cidripv4.extend(record["rdata"])
                    elif record["type"] == "AAAA":
                        Cidripv6.extend(record["rdata"])
                    elif record["type"] == "CNAME":
                        endpoints.extend(record["rdata"])

                properties.append(
                    {
                        "fqdn": fqdn,
                        "type": property["type"],
                        "name": property["name"],
                        "endpoints": endpoints,
                        "Cidripv4": Cidripv4,
                        "Cidripv6": Cidripv6,
                    }
                )
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
