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
    """

    def __init__(self, **akamaiClientKwargs) -> None:
        self.client = AkamaiPropertyClient(**akamaiClientKwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def buildPathKey(self, record: dict) -> dict | None:
        """Return the pathKey dict for a path-eligible rule, or None.

        pathKey is non-null iff path is set (path-eligible rule). The path
        value is the canonical sorted AND-joined criteria string produced by
        extractRuleRecords. A path-eligible rule becomes a Path node ONLY —
        buildRuleKey returns None for it (Path XOR Rule).
        """
        if record["path"] is None:
            return None
        return {"proxy_id": record["propertyId"], "path": record["path"]}

    def buildRuleKey(self, record: dict) -> dict | None:
        """Return the ruleKey dict for an AkamaiPropertyRule node, or None.

        Keyed on (proxy_id, rule_path) — the rule's ordinal tree position — which
        is unique by construction. rule_name is a human label that repeats across
        a property's rule tree (many rules are named "US", "default", etc.), and
        hostname is null for the majority of rules (those not under a hostname
        section), so (proxy_id, rule_name, hostname) is NOT unique and cannot back
        a NODE KEY constraint. rule_path always can.

        Returns None for path-eligible rules so that each rule is EITHER a Path
        node OR an AkamaiPropertyRule, never both (Path XOR Rule). Previously
        ruleKey was always built, so every path-bearing rule was written as both
        a Path and an AkamaiPropertyRule.
        """
        if record["path"] is not None:
            return None
        return {
            "proxy_id": record["propertyId"],
            "rule_path": record["rulePath"],
        }

    async def extractRecordsForProperty(self, property: AkamaiPropertyResponse):
        """Yield pipeline dicts for every rule record in one property."""
        self.logger.info(
            "extracting rule records for property %s (id=%s)",
            property.propertyName,
            property.propertyId,
        )
        ruleTree = self.client.get_rule_tree(
            property_id=property.propertyId,
            version=property.productionVersion,
            contract_id=property.contractId,
            group_id=property.groupId,
        )
        for ruleRecord in self.client.extractRuleRecords(
            rule=ruleTree["rules"],
            propertyId=property.propertyId,
            propertyName=property.propertyName,
            version=property.productionVersion,
            deeplink=property.deeplink,
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

        for property in properties or []:
            if property is None or property.productionVersion is None:
                continue
            try:
                async for recordDict in self.extractRecordsForProperty(property):
                    yield recordDict
            except Exception:
                self.logger.exception(
                    "Failed to extract rule records for property %s (id=%s)",
                    property.propertyName,
                    property.propertyId,
                )
