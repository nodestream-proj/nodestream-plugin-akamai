import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.gtm_client import AkamaiGtmClient


class AkamaiGtmExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiGtmClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for domain in self.client.list_gtm_domains():
            try:
                raw_domain = self.client.get_gtm_domain(domain["name"])
                properties = []
                for property in raw_domain["properties"]:
                    fqdn = property["name"] + "." + raw_domain["name"]
                    servers = []
                    for traffic_target in property["trafficTargets"]:
                        servers.extend(traffic_target["servers"])
                    properties.append(
                        {
                            "fqdn": fqdn,
                            "type": property["type"],
                            "name": property["name"],
                            "trafficTargets": servers,
                        }
                    )
                parsed_domain = {
                    "name": raw_domain["name"],
                    "properties": properties,
                    # "raw": raw_domain,
                }
                print(parsed_domain)
                yield parsed_domain
            except Exception:
                self.logger.error("Failed to get gtm domain: %s", domain["name"])
