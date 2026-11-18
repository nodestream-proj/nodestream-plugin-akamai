from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from nodestream.pipeline.pipeline_file_loader import PipelineFileContents

from nodestream_akamai.waf import AkamaiWafExtractor

WAF_YAML = Path(__file__).parents[2] / "nodestream_akamai" / "waf.yaml"

CONFIG = {
    "id": 11111,
    "name": "ExampleCorp - WAF Security File",
    "productionVersion": 42,
}


def _make_extractor(export):
    extractor = AkamaiWafExtractor(
        base_url="test_url",
        client_token="test_client_token",
        client_secret="test_client_secret",
        access_token="test_access_token",
    )
    extractor.client = MagicMock()
    extractor.client.list_appsec_configs = Mock(return_value=[CONFIG])
    extractor.client.export_appsec_config = Mock(return_value=export)
    return extractor


def _make_policy(policy_id="waf1_123456", name="Production", *, with_waf=True, **extra):
    policy = {"id": policy_id, "name": name, **extra}
    if with_waf:
        policy["webApplicationFirewall"] = {
            "attackGroupActions": [{"group": "SQL", "action": "deny"}]
        }
    return policy


async def _records(export):
    return [r async for r in _make_extractor(export).extract_records()]


# ── policies without a WAF block ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_records_drops_policy_without_waf_block():
    # No webApplicationFirewall block means the WAF is off: no node, no links
    export = {
        "securityPolicies": [
            _make_policy("waf1_1", "With WAF"),
            _make_policy(
                "waf1_2",
                "Without WAF",
                with_waf=False,
                ratePolicyActions=[{"id": 101, "ipv4Action": "deny"}],
            ),
        ]
    }
    records = await _records(export)
    assert [p["policyId"] for p in records[0]["policies"]] == ["waf1_1"]
    assert [r["policyId"] for r in records[1:]] == ["waf1_1"]


@pytest.mark.asyncio
async def test_extract_records_skips_config_without_production_version():
    extractor = _make_extractor({"securityPolicies": []})
    extractor.client.list_appsec_configs = Mock(
        return_value=[{"id": 1, "name": "staging only"}]
    )
    records = [r async for r in extractor.extract_records()]
    assert records == []
    extractor.client.export_appsec_config.assert_not_called()


# ── rate policies, attack groups, reputation profiles ────────────────────────

EXPORT = {
    "rulesets": [
        {
            "attackGroups": [
                {"group": "SQL", "groupName": "SQL Injection"},
                {"group": "XSS", "groupName": "Cross Site Scripting (XSS)"},
            ]
        }
    ],
    "ratePolicies": [
        {
            "id": 101,
            "name": "Login Requests",
            "type": "WAF",
            "averageThreshold": 4,
            "burstThreshold": 5,
            "burstWindow": 5,
            "matchType": "path",
            "used": True,
        },
        {"id": 102, "name": "POST Rate Control", "type": "WAF", "used": True},
        {"id": 103, "name": "Unused", "type": "WAF", "used": False},
    ],
    "reputationProfiles": [
        {
            "id": 201,
            "name": "Web Attackers (High Threat)",
            "context": "WEBATCK",
            "contextReadable": "Web Attackers",
            "enabled": True,
            "threshold": 9,
            "sharedIpHandling": "NON_SHARED",
        },
        {
            "id": 202,
            "name": "Web Scrapers (Low Threat)",
            "context": "WEBSCRP",
            "contextReadable": "Web Scrapers",
            "enabled": False,
            "threshold": 5,
            "sharedIpHandling": "NON_SHARED",
        },
    ],
    "securityPolicies": [
        {
            "id": "waf1_1",
            "name": "Production",
            "securityControls": {
                "applyRateControls": True,
                "applyBotmanControls": True,
                "applyReputationControls": True,
            },
            "webApplicationFirewall": {
                "attackGroupActions": [
                    {"group": "SQL", "action": "deny"},
                    {"group": "XSS", "action": "alert"},
                    {"group": "NEWGROUP", "action": "alert"},
                ]
            },
            "ratePolicyActions": [
                {"id": 101, "ipv4Action": "deny", "ipv6Action": "deny"},
                {"id": 102, "ipv4Action": "alert", "ipv6Action": "none"},
            ],
            "clientReputation": {
                "reputationProfileActions": [{"id": 201, "action": "deny"}]
            },
        },
        {
            "id": "waf1_2",
            "name": "Nothing attached",
            "securityControls": {
                "applyRateControls": False,
                "applyBotmanControls": False,
                "applyReputationControls": False,
            },
            "webApplicationFirewall": {"attackGroupActions": []},
        },
    ],
}


@pytest.mark.asyncio
async def test_extract_records_control_flags_on_policy():
    production, nothing = (await _records(EXPORT))[0]["policies"]
    assert production["rateControlsEnabled"] is True
    assert production["botManagerEnabled"] is True
    assert production["reputationControlsEnabled"] is True
    assert nothing["rateControlsEnabled"] is False
    assert nothing["botManagerEnabled"] is False
    assert nothing["reputationControlsEnabled"] is False


@pytest.mark.asyncio
async def test_extract_records_config_level_definitions_on_config_record():
    config_record = (await _records(EXPORT))[0]
    assert [rp["ratePolicyId"] for rp in config_record["ratePolicies"]] == [
        101,
        102,
        103,
    ]
    assert config_record["ratePolicies"][0] == {
        "configId": 11111,
        "ratePolicyId": 101,
        "name": "Login Requests",
        "type": "WAF",
        "averageThreshold": 4,
        "burstThreshold": 5,
        "burstWindow": 5,
        "matchType": "path",
        "used": True,
    }
    assert config_record["reputationProfiles"][1] == {
        "configId": 11111,
        "reputationProfileId": 202,
        "name": "Web Scrapers (Low Threat)",
        "context": "WEBSCRP",
        "contextReadable": "Web Scrapers",
        "enabled": False,
        "threshold": 5,
        "sharedIpHandling": "NON_SHARED",
    }


@pytest.mark.asyncio
async def test_extract_records_one_policy_record_only_for_policies_with_links():
    records = await _records(EXPORT)
    # config record, then one policy record (waf1_2 has nothing attached)
    assert len(records) == 2
    assert "configId" not in records[1]
    assert records[1] == {
        "policyId": "waf1_1",
        "ratePolicyActions": [
            {
                "configId": 11111,
                "ratePolicyId": 101,
                "ipv4Action": "deny",
                "ipv6Action": "deny",
            },
            {
                "configId": 11111,
                "ratePolicyId": 102,
                "ipv4Action": "alert",
                "ipv6Action": "none",
            },
        ],
        "attackGroupActions": [
            {"group": "SQL", "groupName": "SQL Injection", "action": "deny"},
            {
                "group": "XSS",
                "groupName": "Cross Site Scripting (XSS)",
                "action": "alert",
            },
            {"group": "NEWGROUP", "groupName": None, "action": "alert"},
        ],
        "reputationProfileActions": [
            {"configId": 11111, "reputationProfileId": 201, "action": "deny"}
        ],
    }


@pytest.mark.asyncio
async def test_extract_records_attack_group_name_falls_back_to_static_map():
    export = {"securityPolicies": [_make_policy("waf1_1")]}  # no rulesets
    policy_record = (await _records(export))[1]
    assert policy_record["attackGroupActions"] == [
        {"group": "SQL", "groupName": "SQL Injection", "action": "deny"}
    ]


# ── waf.yaml interpretation ──────────────────────────────────────────────────


def _interpret(records):
    """Run waf.yaml's Interpreter on records; return the valid ingests per record."""
    contents = PipelineFileContents.read_from_file(WAF_YAML)
    interpreter = next(
        step
        for step in contents.step_definitions
        if step.implementation_path.endswith(":Interpreter")
    ).load_step()
    return [
        [
            ctx.desired_ingest
            for ctx in interpreter.interpret_record(record)
            if ctx.desired_ingest.source_node_is_valid
        ]
        for record in records
    ]


def _related(ingest, relationship_type=None):
    return [
        (
            rel.relationship.type,
            rel.to_node if rel.outbound else rel.from_node,
            rel.relationship.properties,
        )
        for rel in ingest.relationships
        if relationship_type in (None, rel.relationship.type)
    ]


@pytest.mark.asyncio
async def test_waf_yaml_config_record_writes_policies_and_definitions():
    config_ingests = _interpret(await _records(EXPORT))[0]

    # Only Pass 1 sources the config; the policy pass is skipped
    assert [i.source.type for i in config_ingests] == ["AkamaiWafConfig"]

    links = _related(config_ingests[0])
    policies = [link for link in links if link[1].type == "AkamaiWafPolicy"]
    definitions = [link for link in links if link[1].type != "AkamaiWafPolicy"]
    assert [(t, n.type, n.key_values["policy_id"]) for t, n, _ in policies] == [
        ("INCLUDED_IN", "AkamaiWafPolicy", "waf1_1"),
        ("INCLUDED_IN", "AkamaiWafPolicy", "waf1_2"),
    ]
    production = policies[0][1].properties
    assert production["rate_controls_enabled"] is True
    assert production["bot_manager_enabled"] is True
    assert production["reputation_controls_enabled"] is True

    assert [(t, n.type, dict(n.key_values)) for t, n, _ in definitions] == [
        (
            "INCLUDED_IN",
            "AkamaiRatePolicy",
            {"config_id": 11111, "rate_policy_id": 101},
        ),
        (
            "INCLUDED_IN",
            "AkamaiRatePolicy",
            {"config_id": 11111, "rate_policy_id": 102},
        ),
        (
            "INCLUDED_IN",
            "AkamaiRatePolicy",
            {"config_id": 11111, "rate_policy_id": 103},
        ),
        (
            "INCLUDED_IN",
            "AkamaiReputationProfile",
            {"config_id": 11111, "reputation_profile_id": 201},
        ),
        (
            "INCLUDED_IN",
            "AkamaiReputationProfile",
            {"config_id": 11111, "reputation_profile_id": 202},
        ),
    ]
    login = definitions[0][1].properties
    assert login["name"] == "Login Requests"
    assert login["average_threshold"] == 4
    assert login["burst_threshold"] == 5
    assert login["used"] is True
    scrapers = definitions[4][1].properties
    assert scrapers["name"] == "Web Scrapers (Low Threat)"
    assert scrapers["context_readable"] == "Web Scrapers"
    assert scrapers["enabled"] is False
    assert scrapers["threshold"] == 5


@pytest.mark.asyncio
async def test_waf_yaml_policy_record_writes_has_relationships_with_actions():
    policy_ingests = _interpret(await _records(EXPORT))[1]

    # Only Pass 2 sources the policy; the config pass is skipped
    assert len(policy_ingests) == 1
    ingest = policy_ingests[0]
    assert ingest.source.type == "AkamaiWafPolicy"
    assert ingest.source.key_values["policy_id"] == "waf1_1"

    rate = _related(ingest, "HAS_RATE_POLICY")
    assert [
        (n.type, n.key_values["rate_policy_id"], p["ipv4_action"], p["ipv6_action"])
        for _, n, p in rate
    ] == [
        ("AkamaiRatePolicy", 101, "deny", "deny"),
        ("AkamaiRatePolicy", 102, "alert", "none"),
    ]

    groups = _related(ingest, "HAS_ATTACK_GROUP")
    assert [
        (n.type, n.key_values["group"], n.properties.get("group_name"), p["action"])
        for _, n, p in groups
    ] == [
        # nodestream lowercases string keys by default
        ("AkamaiAttackGroup", "sql", "SQL Injection", "deny"),
        ("AkamaiAttackGroup", "xss", "Cross Site Scripting (XSS)", "alert"),
        ("AkamaiAttackGroup", "newgroup", None, "alert"),
    ]

    reputation = _related(ingest, "HAS_REPUTATION_PROFILE")
    assert [(n.type, dict(n.key_values), p["action"]) for _, n, p in reputation] == [
        (
            "AkamaiReputationProfile",
            {"config_id": 11111, "reputation_profile_id": 201},
            "deny",
        )
    ]
