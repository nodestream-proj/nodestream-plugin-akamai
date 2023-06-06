import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiAppSecCoverageExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        try:
            configs = self.client.list_appsec_configs()
            for config in configs:
                if 'productionVersion' in config.keys():
                    config['policies'] = self.client.list_appsec_policies(config['id'], config['productionVersion'])
            hostname_coverage = self.client.get_appsec_hostname_coverage()
        except Exception as err:
            self.logger.error("Failed to get appsec hostname coverage: %s", err)
            
        for hostname in hostname_coverage:
            # Only care if hostname is covered
            if hostname['status'] == 'covered':
                # Need to find policy ID, so find first locate config from hostname entry
                covering_config = [config for config in configs if config['id'] == hostname['configuration']['id']][0]
                # Then iterate through policyNames and replace with dict
                for i, policyName in enumerate(hostname['policyNames']):
                    covering_policy = [policy for policy in covering_config['policies'] if policy['policyName'] == policyName][0]
                    hostname['policyNames'][i] = {
                        'policyName': covering_policy['policyName'],
                        'policyId': covering_policy['policyId']
                    }
                yield hostname

def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_appsec_coverage_cacher/pipeline.yaml")
