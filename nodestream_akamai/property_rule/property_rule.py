import dataclasses
import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.model import AkamaiPropertyResponse
from ..akamai_utils.property_client import AkamaiPropertyClient


class AkamaiPropertyRuleExtractor(Extractor):
    """Extracts one record per rule node from AkamaiProperty rule trees.

    For path-eligible rules (has path criteria, no cloudlet conditional),
    the record produces a Path node keyed by the canonical criteria string:

        (AkamaiProperty:Proxy)-[:HAS_PATH]->(Path {path: "/v1/*"})
          -[:ROUTES_TO]->(Endpoint)

    The path key is the full pathCriteria list sorted and joined with AND so
    that each unique combination of criteria maps to exactly one Path node.
    Rules with no path criteria (hostname-only, cloudlet, catch-all) emit one
    record with path=None — Rule node only, no Path node.

    AkamaiPropertyRule is keyed by the rule's structural rule_path because rule
    names and criteria are not unique in Akamai rule trees.
    """

    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiPropertyClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def build_path_key(self, record: dict) -> dict | None:
        """Return the pathKey dict for a path-eligible rule, or None.

        pathKey is non-null iff path is set (path-eligible rule). The path
        value is the canonical sorted AND-joined criteria string produced by
        extractRuleRecords.
        """
        if record["path"] is None:
            return None
        return {"proxy_id": record["propertyId"], "path": record["path"]}

    def build_rule_key(self, record: dict) -> dict:
        """Return the ruleKey dict for an AkamaiPropertyRule node.

        rule_path is the rule's JSON Pointer position in the Akamai rule tree.
        """
        return {
            "proxy_id": record["propertyId"],
            "rule_path": record["rulePath"],
        }

    async def extract_records_for_property(
        self, akamai_property: AkamaiPropertyResponse
    ):
        """Yield pipeline dicts for every rule record in one property."""
        self.logger.info(
            "extracting rule records for property %s (id=%s)",
            akamai_property.propertyName,
            akamai_property.propertyId,
        )
        rule_tree = self.client.get_rule_tree(
            property_id=akamai_property.propertyId,
            version=akamai_property.productionVersion,
            contract_id=akamai_property.contractId,
            group_id=akamai_property.groupId,
        )
        for rule_record in self.client.extractRuleRecords(
            rule=rule_tree["rules"],
            propertyId=akamai_property.propertyId,
            propertyName=akamai_property.propertyName,
            version=akamai_property.productionVersion,
            deeplink=akamai_property.deeplink,
        ):
            record_dict = dataclasses.asdict(rule_record)
            record_dict["pathKey"] = self.build_path_key(record_dict)
            record_dict["ruleKey"] = self.build_rule_key(record_dict)
            yield record_dict

    async def extract_records(self):
        self.logger.debug("extracting property rule records")
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.exception("Failed to list properties: %s", err)
            raise

        for akamai_property in properties or []:
            if akamai_property is None or akamai_property.productionVersion is None:
                continue
            try:
                async for record_dict in self.extract_records_for_property(
                    akamai_property
                ):
                    yield record_dict
            except Exception:
                self.logger.exception(
                    "Failed to extract rule records for property %s (id=%s)",
                    akamai_property.propertyName,
                    akamai_property.propertyId,
                )
