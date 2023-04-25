import logging

from etwpipeline.akamai.client import AkamaiApiClient

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline

class AkamaiNetstorageExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiApiClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_records(self):
        desired_keys = ['storageGroupId', 'storageGroupName', 'domainPrefix', 'estimatedUsageGB']
        upload_domain_suffixes = {
            'ftp': '.ftp.upload.akamai.com',
            'sftp': '.sftp.upload.akamai.com',
            'scp':'.scp.upload.akamai.com',
            'rsync':'.rsync.upload.akamai.com',
            'ssh':'.ssh.upload.akamai.com',
            'aspera':'.aspera.upload.akamai.com',
            'http': '-nsu.upload.akamai.com'
        }
        try:
            netstorage_groups = self.client.list_netstorage_groups()
        except Exception as err:
            self.logger.error("Failed to list netstorage groups: %s", err)

        for group in netstorage_groups:
            parsed_group = {k: v for k, v in group.items() if k in desired_keys}
            # Add uploadDomains dict
            parsed_group['uploadDomains'] = {}
            for suffix in upload_domain_suffixes.keys():
                parsed_group['uploadDomains'][suffix] = parsed_group['domainPrefix'] + upload_domain_suffixes[suffix]
            
            # OPTIONAL: Add raw data output
            #parsed_group['raw'] = group
            yield parsed_group

def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_netstorage_cacher/pipeline.yaml")
