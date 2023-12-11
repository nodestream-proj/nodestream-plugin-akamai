import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.netstorage_client import AkamaiNetstorageClient


class AkamaiNetstorageGroupExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiNetstorageClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        desired_keys = [
            "storageGroupId",
            "storageGroupName",
            "domainPrefix",
            "estimatedUsageGB",
        ]
        upload_domain_suffixes = {
            "ftp": ".ftp.upload.akamai.com",
            "sftp": ".sftp.upload.akamai.com",
            "scp": ".scp.upload.akamai.com",
            "rsync": ".rsync.upload.akamai.com",
            "ssh": ".ssh.upload.akamai.com",
            "aspera": ".aspera.upload.akamai.com",
            "http": "-nsu.upload.akamai.com",
        }
        download_domain = ".download.akamai.com"
        try:
            netstorage_groups = self.client.list_netstorage_groups()
        except Exception as err:
            self.logger.error("Failed to list netstorage groups: %s", err)

        for group in netstorage_groups:
            parsed_group = {k: v for k, v in group.items() if k in desired_keys}
            # Add uploadDomains dict
            parsed_group["uploadDomains"] = {}
            for suffix in upload_domain_suffixes.keys():
                parsed_group["uploadDomains"][suffix] = (
                    parsed_group["domainPrefix"] + upload_domain_suffixes[suffix]
                )
            # Add downloadDomain string
            parsed_group["downloadDomain"] = (
                parsed_group["domainPrefix"] + download_domain
            )

            # OPTIONAL: Add raw data output
            # parsed_group['raw'] = group
            yield parsed_group
