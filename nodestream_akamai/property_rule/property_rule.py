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

    def __init__(self, **akamaiClientKwargs) -> None:
        self.client = AkamaiPropertyClient(**akamaiClientKwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def buildPathKey(self, record: dict) -> dict | None:
        """Return the pathKey dict for a path-eligible rule, or None.

        pathKey is non-null iff path is set (path-eligible rule). The path
        value is the canonical sorted AND-joined criteria string produced by
        extractRuleRecords.
        """
        if record["path"] is None:
            return None
        return {"proxy_id": record["propertyId"], "path": record["path"]}

    def buildRuleKey(self, record: dict) -> dict:
        """Return the ruleKey dict for an AkamaiPropertyRule node.

        rule_path is the rule's JSON Pointer position in the Akamai rule tree.
        """
        return {
            "proxy_id": record["propertyId"],
            "rule_path": record["rule_path"],
        }

    async def extractRecordsForProperty(self, akamai_property: AkamaiPropertyResponse):
        """Yield pipeline dicts for every rule record in one property."""
        self.logger.info(
            "extracting rule records for property %s (id=%s)",
            akamai_property.propertyName,
            akamai_property.propertyId,
        )
        ruleTree = self.client.get_rule_tree(
            property_id=akamai_property.propertyId,
            version=akamai_property.productionVersion,
            contract_id=akamai_property.contractId,
            group_id=akamai_property.groupId,
        )
        for ruleRecord in self.client.extractRuleRecords(
            rule=ruleTree["rules"],
            propertyId=akamai_property.propertyId,
            propertyName=akamai_property.propertyName,
            version=akamai_property.productionVersion,
            deeplink=akamai_property.deeplink,
        ):
            recordDict = dataclasses.asdict(ruleRecord)
            recordDict["pathKey"] = self.buildPathKey(recordDict)
            recordDict["ruleKey"] = self.buildRuleKey(recordDict)
            yield recordDict

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
                async for recordDict in self.extractRecordsForProperty(akamai_property):
                    yield recordDict
            except Exception:
                self.logger.exception(
                    "Failed to extract rule records for property %s (id=%s)",
                    akamai_property.propertyName,
                    akamai_property.propertyId,
                )
