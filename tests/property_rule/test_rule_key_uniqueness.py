"""Regression tests proving the AkamaiPropertyRule key fix on real rule trees.

Background
----------
The original key (proxy_id, rule_name, hostname) was NOT unique: Akamai rule
names repeat across a property's rule tree and hostname is null for most rules.
This produced duplicate AkamaiPropertyRule nodes that could not satisfy a NODE
KEY constraint (Neo.DatabaseError.Schema.ConstraintCreationFailed in prod).

The fix keys AkamaiPropertyRule on (proxy_id, rule_path) — the rule's ordinal
tree position, which is unique by construction — and carries full_path (name
breadcrumb) as a readable property. It also makes Path XOR AkamaiPropertyRule
(a rule is one node type, never both).

These tests run the REAL extractor (AkamaiPropertyClient.extractRuleRecords +
AkamaiPropertyRuleExtractor.build_path_key/build_rule_key) against real, downloaded
production rule trees and assert:

  1. the OLD key (proxy_id, rule_name, hostname) COLLIDES (documents the bug),
  2. the NEW key (proxy_id, rule_path) is UNIQUE (proves the fix),
  3. Path XOR Rule — every record is exactly one bucket,
  4. negative path matches (DOES_NOT_MATCH_ONE_OF) are preserved as !-globs,
  5. full_path is populated and readable.
"""

import dataclasses
import json
import os
from collections import Counter

import pytest

from nodestream_akamai.akamai_utils.property_client import AkamaiPropertyClient
from nodestream_akamai.property_rule import AkamaiPropertyRuleExtractor

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
TREES = [
    "leadgencapability_pm.v21.json",  # qal/e2e sibling rules with repeated names
    "mcp_quickbooks_ion.v4.json",  # already-unique names (regression guard)
]


def _load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def _extract(tree):
    """Run the real extractor over a rule tree and return pipeline record dicts."""
    client = AkamaiPropertyClient(
        base_url="https://x",
        client_token="x",
        client_secret="x",
        access_token="x",
        account_key=None,
    )
    ext = AkamaiPropertyRuleExtractor.__new__(AkamaiPropertyRuleExtractor)
    records = []
    for rr in client.extractRuleRecords(
        rule=tree["rules"],
        propertyId=tree["propertyId"],
        propertyName=tree["propertyName"],
        version=tree["propertyVersion"],
        deeplink="",
    ):
        rec = dataclasses.asdict(rr)
        rec["pathKey"] = ext.build_path_key(rec)
        rec["ruleKey"] = ext.build_rule_key(rec)
        records.append(rec)
    return records


def _old_key(rec):
    """The removed key (proxy_id, rule_name, first-hostname)."""
    host = rec["hostnameCriteria"][0] if rec["hostnameCriteria"] else None
    return (rec["propertyId"], rec["ruleName"], host)


@pytest.mark.parametrize("tree_name", TREES)
def test_new_key_proxy_id_rule_path_is_unique(tree_name):
    """(proxy_id, rule_path) is unique across the whole tree -> constraint creatable."""
    records = _extract(_load(tree_name))
    keys = [
        (r["propertyId"], r["rulePath"]) for r in records if r["ruleKey"] is not None
    ]
    dupes = [k for k, c in Counter(keys).items() if c > 1]
    assert not dupes, f"(proxy_id, rule_path) collisions in {tree_name}: {dupes}"


@pytest.mark.parametrize("tree_name", TREES)
def test_path_xor_rule_never_both(tree_name):
    """Every record is EITHER a Path node OR an AkamaiPropertyRule, never both."""
    records = _extract(_load(tree_name))
    both = [r for r in records if r["pathKey"] is not None and r["ruleKey"] is not None]
    assert not both, f"{len(both)} records are BOTH Path and Rule in {tree_name}"
    for r in records:
        assert (r["pathKey"] is None) != (
            r["ruleKey"] is None
        ), f"record {r['ruleName']} ({r['rulePath']}) is not exactly one bucket"


@pytest.mark.parametrize("tree_name", TREES)
def test_full_path_is_populated_and_contains_rule_name(tree_name):
    records = _extract(_load(tree_name))
    for r in records:
        assert r["fullPath"], f"empty full_path for {r['ruleName']}"
        assert r["ruleName"] in r["fullPath"]


def test_old_key_collides_but_new_key_does_not():
    """The exact production bug (Neo.DatabaseError.Schema.ConstraintCreationFailed):
    two rules named 'US' at different tree positions, both path-less/hostname-less.

    The OLD key (proxy_id, rule_name, hostname) maps both to the SAME key and
    collides. The NEW key (proxy_id, rule_path) keeps them distinct.
    """
    records = _extract(_load("collision_repro.json"))
    rule_records = [r for r in records if r["ruleKey"] is not None]

    # both 'US' rules are present as distinct rule nodes
    us = [r for r in rule_records if r["ruleName"] == "US"]
    assert len(us) == 2, f"expected two 'US' rules, got {len(us)}"

    old_keys = [_old_key(r) for r in us]
    new_keys = [(r["propertyId"], r["rulePath"]) for r in us]

    # OLD key: identical -> would violate NODE KEY (this is the bug)
    assert (
        len(set(old_keys)) == 1
    ), f"expected old key collision, got distinct {old_keys}"
    # NEW key: distinct -> constraint creatable (this is the fix)
    assert (
        len(set(new_keys)) == 2
    ), f"new key must distinguish the two 'US' rules, got {new_keys}"


def test_leadgen_sibling_origin_rules_get_distinct_paths():
    """qal/... and e2e/... origin rules share names but must be distinct nodes,
    disambiguated purely by tree position."""
    records = _extract(_load("leadgencapability_pm.v21.json"))
    by_name = {}
    for r in records:
        if "origin - flowservice" in r["ruleName"]:
            by_name.setdefault(r["ruleName"], set()).add(r["rulePath"])
    # the two 'flowservice' rules (qal + e2e) exist and have different rule_paths
    all_paths = {p for paths in by_name.values() for p in paths}
    assert (
        len(all_paths) >= 2
    ), f"expected distinct tree positions for sibling origin rules, got {by_name}"


def test_negative_path_criteria_preserved_as_negated_glob():
    """'Block Origin Request' uses DOES_NOT_MATCH_ONE_OF; every value must be
    stored as a !-prefixed glob (switch on match operator works as intended)."""
    records = _extract(_load("leadgencapability_pm.v21.json"))
    block = next((r for r in records if r["ruleName"] == "Block Origin Request"), None)
    assert block is not None, "Block Origin Request rule missing"
    negated = [p for p in block["pathCriteria"] if p.startswith("!")]
    assert negated, f"expected negated globs, got {block['pathCriteria']}"
    # all of its criteria are negative -> all values must be !-prefixed
    assert all(
        p.startswith("!") for p in block["pathCriteria"]
    ), f"mixed/incorrect negation encoding: {block['pathCriteria']}"


def test_positive_path_criteria_not_negated():
    """A positive MATCHES_ONE_OF rule ('GraphQL' -> /graphql) must NOT be negated."""
    records = _extract(_load("mcp_quickbooks_ion.v4.json"))
    gql = next((r for r in records if r["ruleName"] == "GraphQL"), None)
    assert gql is not None, "GraphQL rule missing"
    assert "/graphql" in gql["pathCriteria"]
    assert not any(
        p.startswith("!") for p in gql["pathCriteria"]
    ), f"positive match was wrongly negated: {gql['pathCriteria']}"


def test_cloudfront_path_rule_routes_to_origin_as_path_node():
    """Origins/Cloudfront (/web_assets/* + origin) is a Path node, ROUTES_TO cf,
    content preserved."""
    records = _extract(_load("mcp_quickbooks_ion.v4.json"))
    cf = next((r for r in records if r["ruleName"] == "Cloudfront"), None)
    assert cf is not None
    assert cf["pathKey"] is not None and cf["ruleKey"] is None  # Path node only
    assert "/web_assets/*" in cf["pathCriteria"]
    assert cf["originHostname"] == "d2l8cmvpwpdfrn.cloudfront.net"
