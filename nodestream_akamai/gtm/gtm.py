import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils import addresses
from ..akamai_utils.gtm_client import AkamaiGtmClient

PARSED_PROPERTY_TYPES = [
    "weighted-round-robin",
    "weighted-hashed",
    "weighted-round-robin-load-feedback",
    "ranked-failover",
    "failover",
    "performance",
]
DEEPLINK_PREFIX = "https://control.akamai.com/apps/gtm/#/domains/"


class AkamaiGtmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiGtmClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for domain in self.client.list_gtm_domains():
            try:
                raw_domain = self.client.get_gtm_domain(domain["name"])
            except Exception as err:
                self.logger.error(
                    "Failed to get gtm domain: %s",
                    domain["name"],
                    exc_info=True,
                )
                raise err

            deeplink = f'{DEEPLINK_PREFIX}{domain["name"]}/properties/list'
            properties = []
            for prop in raw_domain["properties"]:
                out_property = {
                    "fqdn": f'{prop["name"]}.{raw_domain["name"]}',
                    "type": prop["type"],
                    "name": prop["name"],
                    "Endpoint": [],
                    "Cidripv4": [],
                    "Cidripv6": [],
                }

                if prop["type"] in PARSED_PROPERTY_TYPES:
                    for traffic_target in prop["trafficTargets"]:
                        if len(traffic_target["servers"]) > 0:
                            for server in traffic_target["servers"]:
                                address_format = addresses.get_format(server)
                                node_type = address_format.node_type
                                if node_type:
                                    out_property[node_type].append(server)
                        if traffic_target["handoutCName"]:
                            out_property["Endpoint"].append(
                                traffic_target["handoutCName"]
                            )
                for rrset in prop["staticRRSets"]:
                    for record in rrset["rdata"]:
                        address_format = addresses.get_format(record)
                        node_type = address_format.node_type
                        if node_type:
                            out_property[node_type].append(record)

                properties.append(out_property)

            yield {
                "name": raw_domain["name"],
                "properties": properties,
                "type": raw_domain["type"],
                "loadImbalancePercentage": raw_domain["loadImbalancePercentage"],
                "loadFeedback": raw_domain["loadFeedback"],
                "cnameCoalescingEnabled": raw_domain["cnameCoalescingEnabled"],
                "deeplink": deeplink,
            }
