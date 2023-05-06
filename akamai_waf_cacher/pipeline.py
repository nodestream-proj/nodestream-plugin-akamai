import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


class AkamaiWAFExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        ag_map = {
            'POLICY':'Web Policy Violation',
            'WAT':'Web Attack Tool',
            'PROTOCOL':'Web Protocol Attack',
            'SQL':'SQL Injection',
            'XSS':'Cross Site Scripting',
            'CMD':'Command Injection',
            'LFI':'Local File Inclusion',
            'RFI':'Remote File Inclusion',
            'PLATFORM':'Web Platform Attack',
            'OUTBOUND':'Total Outbound'
        }

        for config in self.client.list_appsec_configs():
            # try:
                export = self.client.export_appsec_config(config_id = config['id'], config_version = config['productionVersion'])
                # Construct output dict
                output_config = {
                    'configId': config['id'],
                    'configName': config['name'],
                    'productionVersion': config['productionVersion'],
                    'policies': []
                }
                # Iterate through policies and add custom dict to output
                for policy in export['securityPolicies']:
                    output_policy = {
                        'policyId': policy['id'],
                        'policyName': policy['name'],
                        'attackGroupActions': []
                    }
                    if 'webApplicationFirewall' in policy.keys():
                        for action in policy['webApplicationFirewall']['attackGroupActions']:
                            output_policy['attackGroupActions'].append({
                                    'group': action['group'],
                                    'groupName': ag_map[action['group']],
                                    'action': action['action']
                                }
                            )
                        output_config['policies'].append(output_policy)
                
                yield output_config
            # except Exception as err:
            #     self.logger.error(f"Failed to export appsec configuration {config['name']}: {err}")


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_waf_cacher/pipeline.yaml")
