import dataclasses
import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.property_client import AkamaiPropertyClient


class AkamaiPropertyRuleExtractor(Extractor):
    """Extracts per-positive-glob records from AkamaiProperty rule trees.

    For path-eligible rules (no hostname dimension, no cloudlet conditional),
    one record is emitted per positive (non-negated) path glob so the pipeline
    produces one simple allowlist Path node per glob:

        (AkamaiProperty:Proxy)-[:HAS_PATH]->(Path {path: "/v1/*"})
          -[:ROUTES_TO]->(Endpoint)

    The full compound pathCriteria (including negations) is retained on every
    record so the AkamaiPropertyRule node receives the complete expression.
    ruleKey is stable across all fan-out records for the same rule, so the
    Rule node is upserted idempotently.

    Rules with zero positive globs (pure-negation, hostname-only, cloudlet,
    catch-all) emit one record with path=None — Rule node only, no Path node.
    """

    def __init__(self, **akamaiClientKwargs) -> None:
        self.client = AkamaiPropertyClient(**akamaiClientKwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        self.logger.debug("extracting property rule records")
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.exception("Failed to list properties: %s", err)
            raise

        for prop in (properties or []):
            if prop is None or prop.get("productionVersion") is None:
                continue
            self.logger.info(
                "extracting rule records for property %s (id=%s)",
                prop.get("propertyName"),
                prop.get("propertyId"),
            )
            try:
                version = prop["productionVersion"]
                ruleTree = self.client.get_rule_tree(
                    property_id=prop["propertyId"],
                    version=version,
                    contract_id=prop["contractId"],
                    group_id=prop["groupId"],
                )
                deeplink = (
                    "https://control.akamai.com/apps/property-manager/"
                    f"#/property-version/{prop['assetId']}/{version}/edit"
                    f"?gid={prop['groupId']}"
                )
                for record in self.client.extractRuleRecords(
                    rule=ruleTree["rules"],
                    propertyId=prop["propertyId"],
                    propertyName=prop["propertyName"],
                    version=version,
                    deeplink=deeplink,
                ):
                    d = dataclasses.asdict(record)
                    # pathKey: non-null iff this record represents a single positive glob.
                    # path is already set to the individual glob (or None) by extractRuleRecords.
                    d["pathKey"] = {"proxy_id": d["proxyId"], "path": d["path"]} if d["path"] else None
                    # ruleKey includes hostname so that two rules with the same name but
                    # different hostname criteria produce distinct AkamaiPropertyRule nodes.
                    # hostname_criteria is None for rules with no hostname dimension.
                    hostname = d["hostnameCriteria"][0] if d["hostnameCriteria"] else None
                    d["ruleKey"] = {"proxy_id": d["proxyId"], "rule_name": d["ruleName"], "hostname": hostname}
                    yield d
            except Exception:
                self.logger.exception(
                    "Failed to extract rule records for property %s (id=%s)",
                    prop.get("propertyName"),
                    prop.get("propertyId"),
                )
