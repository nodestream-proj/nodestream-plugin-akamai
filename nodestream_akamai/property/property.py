import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.iam_client import AkamaiIamClient
from ..akamai_utils.property_client import AkamaiPropertyClient


class AkamaiPropertyExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiPropertyClient(**akamai_client_kwargs)
        self.iam_client = AkamaiIamClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.error("Failed to list properties: %s", err)
            return

        try:
            hostnames = self.client.list_all_hostnames()
        except Exception as err:
            self.logger.error("Failed to list hostnames: %s", err)
            return

        try:
            iam_properties = self.iam_client.list_properties()
        except Exception as err:
            self.logger.error("Failed to list IAM properties: %s", err)
            return

        production_active_properties = [
            property
            for property in properties
            if property["productionVersion"] is not None
        ]
        for property in production_active_properties:
            matching_host = [
                hostname
                for hostname in hostnames
                if hostname["propertyId"] == property["propertyId"]
            ]
            property["contractId"] = None
            property["groupId"] = None
            if len(matching_host) > 0:
                property["contractId"] = matching_host[0]["contractId"]
                property["groupId"] = matching_host[0]["groupId"]

            matching_iam_property = [
                i
                for i in iam_properties
                if i["propertyName"] == property["propertyName"].lower()
            ]
            if matching_iam_property:
                property["assetId"] = matching_iam_property[0]["propertyId"]
            else:
                self.logger.warning(
                    f"""Failed to find an IAM property named '{property["propertyName"]}'"""
                )

            try:
                described_property = self.client.describe_property_by_dict(property)
                if described_property.name == "hello.stuartmacleod.net":
                    print(described_property)
                yield described_property.as_eventbus_json()
            except Exception as err:
                self.logger.error(
                    "Failed to get property: {p}, {e}".format(
                        p=property["propertyId"], e=err
                    )
                )
