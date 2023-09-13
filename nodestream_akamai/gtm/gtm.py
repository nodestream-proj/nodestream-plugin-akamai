import logging

from ..akamai_utils.client import AkamaiApiClient

from nodestream.pipeline.extractors import Extractor


class AkamaiGTMExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        for domain in self.client.list_gtm_domains():
            try:
                raw_domain = self.client.get_gtm_domain(domain['name'])
                summary = []
                for property in raw_domain['properties']:
                    fqdn = property['name'] + '.' + raw_domain['name']
                    summary.append({
                        'fqdn': fqdn,
                        'trafficTargets': property['trafficTargets']
                    })
                parsed_domain = {
                    'name': raw_domain['name'],
                    'summary': summary,
                    'raw': raw_domain
                }
                yield parsed_domain
            except Exception:
                self.logger.error("Failed to get gtm domain: %s", domain['name'])
