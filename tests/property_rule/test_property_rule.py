"""Tests for AkamaiPropertyRuleExtractor.

Covers all branches of extract_records:
  - list_all_properties raises → propagated to caller
  - property with no productionVersion skipped
  - property with None skipped
  - get_rule_tree / extractRuleRecords raises → logged, continues
  - successful extraction → pathKey and ruleKey set correctly
  - path-eligible rule (path set) → pathKey non-null
  - non-path rule (path None) → pathKey is None
  - duplicate semantic rules → ruleKey differs by rule_path
"""

from unittest.mock import MagicMock, Mock

import pytest
from requests import HTTPError

from nodestream_akamai.akamai_utils.model import (
    AkamaiPropertyResponse,
    PropertyRuleRecord,
)
from nodestream_akamai.property_rule import AkamaiPropertyRuleExtractor


def _make_extractor():
    extractor = AkamaiPropertyRuleExtractor(
        base_url="test_url",
        client_token="test_client_token",
        client_secret="test_client_secret",
        access_token="test_access_token",
    )
    extractor.client = MagicMock()
    return extractor


def _make_property(
    property_id="prp_123",
    property_name="my-property",
    production_version=5,
    asset_id="10001",
    contract_id="ctr_ABC",
    group_id="grp_1",
):
    return AkamaiPropertyResponse(
        propertyId=property_id,
        propertyName=property_name,
        productionVersion=production_version,
        assetId=asset_id,
        contractId=contract_id,
        groupId=group_id,
    )


def _make_record(
    property_id="prp_123",
    path="/v1/*",
    path_criteria=None,
    hostname_criteria=None,
    origin_hostname="backend.example.com",
    rule_name="v1-api",
    rule_depth=1,
    rule_path="/rules/children/0",
):
    return PropertyRuleRecord(
        path=path,
        pathCriteria=path_criteria or ["/v1/*"],
        hostnameCriteria=hostname_criteria or [],
        conditionalOriginId=None,
        originHostname=origin_hostname,
        originType="CUSTOMER",
        outboundPath=None,
        baseDirectory=None,
        rulePath=rule_path,
        ruleName=rule_name,
        ruleDepth=rule_depth,
        criteriaMustSatisfy="all",
        securityBehaviors=[],
        propertyId=property_id,
        propertyName="my-property",
        version=5,
        deeplink="https://example.com/deeplink",
    )


# ── list_all_properties failure ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_records_list_props_raises():
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(side_effect=HTTPError("network error"))
    with pytest.raises(HTTPError):
        _ = [x async for x in extractor.extract_records()]


# ── skipped properties ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_records_skips_none_prop():
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(return_value=[None])
    result = [x async for x in extractor.extract_records()]
    assert result == []
    extractor.client.get_rule_tree.assert_not_called()


@pytest.mark.asyncio
async def test_extract_records_skips_prop_without_production_version():
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(
        return_value=[_make_property(production_version=None)]
    )
    result = [x async for x in extractor.extract_records()]
    assert result == []
    extractor.client.get_rule_tree.assert_not_called()


@pytest.mark.asyncio
async def test_extract_records_skips_prop_with_null_production_version():
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(
        return_value=[_make_property(production_version=None)]
    )
    result = [x async for x in extractor.extract_records()]
    assert result == []


# ── get_rule_tree / extractRuleRecords failure ────────────────────────────────


@pytest.mark.asyncio
async def test_extract_records_rule_tree_raises_continues():
    """Exception during rule tree fetch is logged and the property is skipped."""
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(return_value=[_make_property()])
    extractor.client.get_rule_tree = Mock(side_effect=RuntimeError("API down"))
    result = [x async for x in extractor.extract_records()]
    assert result == []


# ── successful extraction ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_records_path_eligible_rule():
    """A path-eligible record (path set) produces a non-null pathKey."""
    extractor = _make_extractor()
    akamai_property = _make_property()
    record = _make_record(path="/v1/*", path_criteria=["/v1/*"])
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})
    extractor.client.extractRuleRecords = Mock(return_value=[record])

    results = [x async for x in extractor.extract_records()]

    assert len(results) == 1
    d = results[0]
    assert d["pathKey"] == {"proxy_id": "prp_123", "path": "/v1/*"}
    assert d["rulePath"] == "/rules/children/0"
    assert "rule_path" not in d
    assert d["ruleKey"] == {"proxy_id": "prp_123", "rule_path": "/rules/children/0"}


@pytest.mark.asyncio
async def test_extract_records_non_path_rule_pathkey_none():
    """A non-path rule (path=None) produces pathKey=None."""
    extractor = _make_extractor()
    akamai_property = _make_property()
    record = _make_record(path=None, path_criteria=[])
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})
    extractor.client.extractRuleRecords = Mock(return_value=[record])

    results = [x async for x in extractor.extract_records()]

    assert len(results) == 1
    assert results[0]["pathKey"] is None


@pytest.mark.asyncio
async def test_extract_records_rulekey_ignores_hostname_criteria():
    """ruleKey uses rule_path, not hostname criteria."""
    extractor = _make_extractor()
    akamai_property = _make_property()
    record = _make_record(
        path="/v1/*",
        hostname_criteria=["api.example.com", "api2.example.com"],
    )
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})
    extractor.client.extractRuleRecords = Mock(return_value=[record])

    results = [x async for x in extractor.extract_records()]

    assert results[0]["ruleKey"] == {
        "proxy_id": "prp_123",
        "rule_path": "/rules/children/0",
    }


@pytest.mark.asyncio
async def test_extract_records_rulekey_excludes_rule_name_and_hostname():
    """Semantic fields remain metadata, not identity."""
    extractor = _make_extractor()
    akamai_property = _make_property()
    record = _make_record(path=None, hostname_criteria=[])
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})
    extractor.client.extractRuleRecords = Mock(return_value=[record])

    results = [x async for x in extractor.extract_records()]

    assert "rule_name" not in results[0]["ruleKey"]
    assert "hostname" not in results[0]["ruleKey"]


def test_build_rulekey_distinguishes_duplicate_semantics_by_rule_path():
    extractor = _make_extractor()
    first = {"propertyId": "501159", "rulePath": "/rules/children/0"}
    second = {"propertyId": "501159", "rulePath": "/rules/children/1"}

    assert extractor.build_rule_key(first) != extractor.build_rule_key(second)


@pytest.mark.asyncio
async def test_extract_records_deeplink_constructed_correctly():
    """deeplink is built from assetId, version, and groupId."""
    extractor = _make_extractor()
    akamai_property = _make_property(
        asset_id="99999", production_version=7, group_id="grp_42"
    )
    record = _make_record()
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})

    captured_deeplink = {}

    def capture_records(**kwargs):
        captured_deeplink["deeplink"] = kwargs.get("deeplink", "")
        return [record]

    extractor.client.extractRuleRecords = Mock(side_effect=capture_records)

    _ = [x async for x in extractor.extract_records()]

    assert captured_deeplink["deeplink"] == (
        "https://control.akamai.com/apps/property-manager/"
        "#/property-version/99999/7/edit?gid=grp_42"
    )


@pytest.mark.asyncio
async def test_extract_records_multiple_records_from_one_property():
    """Multiple rule records from a single property are all yielded."""
    extractor = _make_extractor()
    akamai_property = _make_property()
    records = [
        _make_record(path="/v1/*", rule_name="v1"),
        _make_record(path=None, rule_name="default", rule_depth=0),
    ]
    extractor.client.list_all_properties = Mock(return_value=[akamai_property])
    extractor.client.get_rule_tree = Mock(return_value={"rules": {}})
    extractor.client.extractRuleRecords = Mock(return_value=records)

    results = [x async for x in extractor.extract_records()]
    assert len(results) == 2


@pytest.mark.asyncio
async def test_extract_records_empty_properties():
    """Empty property list yields nothing."""
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(return_value=[])
    result = [x async for x in extractor.extract_records()]
    assert result == []


@pytest.mark.asyncio
async def test_extract_records_none_properties():
    """None return from list_all_properties yields nothing."""
    extractor = _make_extractor()
    extractor.client.list_all_properties = Mock(return_value=None)
    result = [x async for x in extractor.extract_records()]
    assert result == []
