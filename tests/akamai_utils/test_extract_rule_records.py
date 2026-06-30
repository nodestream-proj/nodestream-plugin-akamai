"""Tests for AkamaiPropertyClient.extractRuleRecords and extractRuleCriteria.

Key invariants verified:
  1. path_criteria is a flat List[str] of individual glob patterns (micromatch-ready).
  2. The path node key equals PATH_AND.join(path_criteria) — stable, deterministic.
  3. Ancestor criteria are inherited (prepended) by child rules.
  4. hostname_criteria is kept separate from path_criteria.
  5. Negated criteria are prefixed with "!" in the list elements.
  6. Path eligibility is true iff path criteria exist and no cloudlet conditional exists.
  7. Security behaviors are mapped to normalized names.
  8. rulePath is the JSON Pointer location of the rule in the tree.
"""

import pytest

from nodestream_akamai.akamai_utils.property_client import (
    PATH_AND,
    AkamaiPropertyClient,
)


@pytest.fixture
def client():
    return AkamaiPropertyClient(
        base_url="url",
        client_token="ctoken",
        client_secret="secret",
        access_token="atoken",
    )


def _make_rule(
    name, criteria=None, behaviors=None, children=None, criteria_must_satisfy="all"
):
    return {
        "name": name,
        "criteria": criteria or [],
        "behaviors": behaviors or [],
        "children": children or [],
        "criteriaMustSatisfy": criteria_must_satisfy,
    }


def _path_criterion(values, *, negative=False):
    return {
        "name": "path",
        "options": {
            "matchOperator": "DOES_NOT_MATCH_ONE_OF" if negative else "MATCHES_ONE_OF",
            "values": values,
        },
    }


def _hostname_criterion(values, *, negative=False):
    return {
        "name": "hostname",
        "options": {
            "matchOperator": "IS_NOT_ONE_OF" if negative else "IS_ONE_OF",
            "values": values,
        },
    }


def _origin_behavior(hostname="backend.example.com", origin_type="CUSTOMER"):
    return {
        "name": "origin",
        "options": {"originType": origin_type, "hostname": hostname},
    }


def _security_behavior(name, *, enabled=True):
    return {"name": name, "options": {"enabled": enabled}}


# ── extractRuleCriteria ────────────────────────────────────────────────────────


def test_extract_rule_criteria_empty_rule(client):
    rule = _make_rule("default")
    path_criteria, hostname_criteria, conditional_origin_id = (
        client.extractRuleCriteria(rule)
    )
    assert path_criteria == []
    assert hostname_criteria == []
    assert conditional_origin_id is None


def test_extract_rule_criteria_single_positive_path(client):
    rule = _make_rule("api", criteria=[_path_criterion(["/v1/*"])])
    path_criteria, hostname_criteria, _ = client.extractRuleCriteria(rule)
    assert path_criteria == ["/v1/*"]
    assert hostname_criteria == []


def test_extract_rule_criteria_multiple_path_values_same_criterion(client):
    """Multiple values in one criterion block = OR semantics = flat list elements."""
    rule = _make_rule("api", criteria=[_path_criterion(["/v1/*", "/v2/*"])])
    path_criteria, _, _ = client.extractRuleCriteria(rule)
    # Each value is its own list element — not joined — micromatch-ready
    assert path_criteria == ["/v1/*", "/v2/*"]


def test_extract_rule_criteria_negative_path_prefixed(client):
    rule = _make_rule(
        "no-sitemap",
        criteria=[_path_criterion(["/community/sitemap*.xml"], negative=True)],
    )
    path_criteria, _, _ = client.extractRuleCriteria(rule)
    assert path_criteria == ["!/community/sitemap*.xml"]


def test_extract_rule_criteria_hostname_criterion_separate(client):
    rule = _make_rule("host-rule", criteria=[_hostname_criterion(["api.example.com"])])
    path_criteria, hostname_criteria, _ = client.extractRuleCriteria(rule)
    assert path_criteria == []
    assert hostname_criteria == ["api.example.com"]


def test_extract_rule_criteria_mixed_path_and_hostname(client):
    rule = _make_rule(
        "mixed",
        criteria=[
            _path_criterion(["/v1/*"]),
            _hostname_criterion(["api.example.com"]),
        ],
    )
    path_criteria, hostname_criteria, _ = client.extractRuleCriteria(rule)
    assert path_criteria == ["/v1/*"]
    assert hostname_criteria == ["api.example.com"]


def test_extract_rule_criteria_cloudlets_origin_extracted(client):
    rule = _make_rule(
        "cloudlet-route",
        criteria=[
            {
                "name": "cloudletsOrigin",
                "options": {"originId": "dc1_impot_ca_prod"},
            }
        ],
    )
    _, _, conditional_origin_id = client.extractRuleCriteria(rule)
    assert conditional_origin_id == "dc1_impot_ca_prod"


# ── extractRuleRecords: basic structure ───────────────────────────────────────


def test_extract_rule_records_default_rule_only(client):
    """Root rule with no criteria and an origin emits one record with path=None."""
    root = _make_rule("default", behaviors=[_origin_behavior("backend.example.com")])
    records = client.extractRuleRecords(
        rule=root,
        propertyId="prp_123",
        propertyName="my-property",
        version=5,
        deeplink="https://example.com/deeplink",
    )
    assert len(records) == 1
    r = records[0]
    assert r.propertyId == "prp_123"
    assert r.path is None  # no criteria at root → no path key
    assert r.pathCriteria == []
    assert r.hostnameCriteria == []
    assert r.originHostname == "backend.example.com"
    assert r.rulePath == "/rules"
    assert r.ruleDepth == 0
    assert r.ruleName == "default"


def test_extract_rule_records_single_child_path_rule(client):
    """Child with its own origin; root has no origin so only child is emitted."""
    child = _make_rule(
        "v1-api",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[_origin_behavior("api-backend.example.com")],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root,
        propertyId="prp_456",
        propertyName="api-property",
        version=3,
        deeplink="",
    )
    # root has no origin → omitted; only child emitted
    assert len(records) == 1
    child_record = records[0]
    assert child_record.rulePath == "/rules/children/0"
    assert child_record.pathCriteria == ["/v1/*"]
    assert child_record.path == "/v1/*"
    assert child_record.ruleDepth == 1
    assert child_record.originHostname == "api-backend.example.com"


def test_extract_rule_records_compound_rule_emits_one_record(client):
    """A compound rule (positive + negation) emits exactly one record.

    path = sorted path_criteria joined with AND; full path_criteria list
    is retained on the record for micromatch evaluation.
    """
    child = _make_rule(
        "community",
        criteria=[
            _path_criterion(["/community/*"]),
            _path_criterion(["/community/sitemap*.xml"], negative=True),
        ],
        behaviors=[_origin_behavior("community-backend.example.com")],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_789", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 1
    child_record = records[0]
    # path is the sorted AND-join of all criteria
    assert child_record.path == "!/community/sitemap*.xml AND /community/*"
    # full compound criteria still present on the record
    assert child_record.pathCriteria == ["/community/*", "!/community/sitemap*.xml"]


def test_extract_rule_records_criteria_inherited_from_ancestors(client):
    """A grandchild rule's path_criteria includes criteria from root → parent → child.

    Root and parent have no origin → both omitted. Grandchild emits one record
    with path = sorted AND-join of all accumulated criteria.
    """
    parent = _make_rule(
        "community",
        criteria=[_path_criterion(["/community/*"])],
        children=[
            _make_rule(
                "community-api",
                criteria=[_path_criterion(["/community/api/*"])],
                behaviors=[_origin_behavior("community-api-backend.example.com")],
            )
        ],
    )
    root = _make_rule("default", children=[parent])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_gc", propertyName="p", version=1, deeplink=""
    )
    # One record: path = sorted AND-join of inherited + own criteria
    assert len(records) == 1
    r = records[0]
    assert r.rulePath == "/rules/children/0/children/0"
    assert r.path == "/community/* AND /community/api/*"
    assert r.pathCriteria == ["/community/*", "/community/api/*"]
    assert r.ruleDepth == 2


def test_extract_rule_records_hostname_rule_not_path(client):
    """A rule with hostname criteria only (no path criteria) emits one record with path=None."""
    child = _make_rule(
        "host-rule",
        criteria=[_hostname_criterion(["api.example.com"])],
        behaviors=[_origin_behavior("backend.example.com")],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_h", propertyName="p", version=1, deeplink=""
    )
    # root has no origin → omitted; only child emitted
    assert len(records) == 1
    host_record = records[0]
    assert host_record.pathCriteria == []
    assert host_record.hostnameCriteria == ["api.example.com"]
    # No path criteria → not path-eligible → path is None
    assert host_record.path is None


def test_extract_rule_records_pure_path_rule_is_path_eligible(client):
    """A rule with only path criteria produces a record with a non-null path (Path-eligible)."""
    child = _make_rule(
        "v1",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[_origin_behavior()],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_p", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 1
    r = records[0]
    assert r.path == "/v1/*"


def test_extract_rule_records_mixed_path_hostname_is_path_eligible(client):
    """A rule with both path and hostname criteria still produces a Path node.

    Hostname scopes which ingress traffic hits the path, but the path glob itself
    is a genuine allowlist entry. The AkamaiPropertyRule retains the full compound
    expression; the Path node captures the simple allowlist glob.
    """
    child = _make_rule(
        "mixed",
        criteria=[
            _path_criterion(["/v1/*"]),
            _hostname_criterion(["api.example.com"]),
        ],
        behaviors=[_origin_behavior()],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_m", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 1
    r = records[0]
    # path+hostname → path-eligible → path is the positive glob
    assert r.path == "/v1/*"
    assert r.hostnameCriteria == ["api.example.com"]


def test_extract_rule_records_duplicate_semantics_get_distinct_rule_paths(client):
    first = _make_rule(
        "Account Manager Cross Domain /app/unsubscribe Redirect ",
        criteria=[_hostname_criterion(["*.intuit.com"], negative=True)],
        behaviors=[_origin_behavior("first-backend.example.com")],
    )
    second = _make_rule(
        "Account Manager Cross Domain /app/unsubscribe Redirect ",
        criteria=[_hostname_criterion(["*.intuit.com"], negative=True)],
        behaviors=[_origin_behavior("second-backend.example.com")],
    )
    root = _make_rule("default", children=[first, second])

    records = client.extractRuleRecords(
        rule=root, propertyId="501159", propertyName="p", version=1, deeplink=""
    )

    assert [r.rulePath for r in records] == [
        "/rules/children/0",
        "/rules/children/1",
    ]
    assert records[0].ruleName == records[1].ruleName
    assert records[0].hostnameCriteria == records[1].hostnameCriteria


def test_extract_rule_records_rule_path_keeps_skipped_child_indexes(client):
    first = _make_rule("first", behaviors=[_origin_behavior("first.example.com")])
    skipped = _make_rule("skipped-no-origin")
    third = _make_rule("third", behaviors=[_origin_behavior("third.example.com")])
    root = _make_rule("default", children=[first, skipped, third])

    records = client.extractRuleRecords(
        rule=root, propertyId="prp_skip", propertyName="p", version=1, deeplink=""
    )

    assert [r.rulePath for r in records] == [
        "/rules/children/0",
        "/rules/children/2",
    ]


# ── Security behaviors ─────────────────────────────────────────────────────────


def test_extract_security_behaviors_maps_known_names(client):
    behaviors = [
        _security_behavior("edgeAuth"),
        _security_behavior("siteShield"),
        _security_behavior("tokenAuth"),
    ]
    result = client.extractSecurityBehaviors(behaviors)
    assert set(result) == {
        "AKAMAI_EDGE_AUTH",
        "AKAMAI_SITE_SHIELD",
        "AKAMAI_TOKEN_AUTH",
    }


def test_extract_security_behaviors_disabled_excluded(client):
    behaviors = [_security_behavior("edgeAuth", enabled=False)]
    assert client.extractSecurityBehaviors(behaviors) == []


def test_extract_security_behaviors_unknown_behavior_ignored(client):
    behaviors = [{"name": "gzipResponse", "options": {"enabled": True}}]
    assert client.extractSecurityBehaviors(behaviors) == []


def test_extract_rule_records_security_behaviors_on_record(client):
    """Security behaviors found in a rule are included in the record."""
    child = _make_rule(
        "protected",
        criteria=[_path_criterion(["/secure/*"])],
        behaviors=[
            _origin_behavior(),
            _security_behavior("edgeAuth"),
        ],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_s", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 1
    assert records[0].securityBehaviors == ["AKAMAI_EDGE_AUTH"]


# ── Micromatch compatibility invariant ────────────────────────────────────────


def test_path_criteria_elements_have_no_and_separator(client):
    """No individual path_criteria element should contain PATH_AND — that would
    mean AND-joined strings leaked into the list, making them incompatible with
    micromatch's pattern-per-element expectation."""
    child = _make_rule(
        "complex",
        criteria=[
            _path_criterion(["/community/*", "/api/*"]),
            _path_criterion(["/community/sitemap*.xml"], negative=True),
        ],
        behaviors=[_origin_behavior()],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_mc", propertyName="p", version=1, deeplink=""
    )
    # One record (one rule); path_criteria list elements must never contain PATH_AND
    assert len(records) == 1
    for r in records:
        for element in r.pathCriteria:
            assert PATH_AND not in element, (
                f"path_criteria element {element!r} contains PATH_AND — "
                "would break micromatch compatibility"
            )


def test_path_is_canonical_sorted_and_join(client):
    """path is the sorted path_criteria joined with AND — one record per rule."""
    child = _make_rule(
        "multi",
        criteria=[
            _path_criterion(["/v1/*", "/v2/*"]),
            _path_criterion(["/v1/health"], negative=True),
        ],
        behaviors=[_origin_behavior()],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_k", propertyName="p", version=1, deeplink=""
    )
    # One rule → one record; path = sorted AND-join
    assert len(records) == 1
    r = records[0]
    assert r.pathCriteria == ["/v1/*", "/v2/*", "!/v1/health"]
    assert r.path == "!/v1/health AND /v1/* AND /v2/*"


# ── Origin inheritance ─────────────────────────────────────────────────────────


def test_extract_rule_records_child_inherits_root_origin(client):
    """Child with no own origin inherits origin from root (default rule)."""
    child = _make_rule(
        "v1-api",
        criteria=[_path_criterion(["/v1/*"])],
    )
    root = _make_rule(
        "default",
        behaviors=[_origin_behavior("root-backend.example.com")],
        children=[child],
    )
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_inh", propertyName="p", version=1, deeplink=""
    )
    # root emits 1 (depth=0, no criteria, path=None) + child inherits origin (depth=1, path="/v1/*")
    assert len(records) == 2
    root_record = next(r for r in records if r.ruleDepth == 0)
    child_record = next(r for r in records if r.ruleDepth == 1)
    assert root_record.originHostname == "root-backend.example.com"
    assert root_record.path is None
    assert child_record.originHostname == "root-backend.example.com"
    assert child_record.path == "/v1/*"
    assert child_record.pathCriteria == ["/v1/*"]


def test_extract_rule_records_grandchild_inherits_root_origin(client):
    """Grandchild inherits origin from root when neither parent nor grandchild re-declare one."""
    grandchild = _make_rule(
        "community-api",
        criteria=[_path_criterion(["/community/api/*"])],
    )
    parent = _make_rule(
        "community",
        criteria=[_path_criterion(["/community/*"])],
        children=[grandchild],
    )
    root = _make_rule(
        "default",
        behaviors=[_origin_behavior("shared-backend.example.com")],
        children=[parent],
    )
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_gc_inh", propertyName="p", version=1, deeplink=""
    )
    # root: 1 record (path=None)
    # parent: 1 record (path="/community/*")
    # grandchild: 1 record (path="/community/* AND /community/api/*")
    assert len(records) == 3
    for r in records:
        assert r.originHostname == "shared-backend.example.com"
    gc_records = [r for r in records if r.ruleDepth == 2]
    assert len(gc_records) == 1
    assert gc_records[0].path == "/community/* AND /community/api/*"
    assert gc_records[0].pathCriteria == ["/community/*", "/community/api/*"]


def test_extract_rule_records_child_origin_overrides_inherited(client):
    """Child that re-declares its own origin uses it, not the inherited one."""
    child = _make_rule(
        "v1-api",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[_origin_behavior("child-backend.example.com")],
    )
    root = _make_rule(
        "default",
        behaviors=[_origin_behavior("root-backend.example.com")],
        children=[child],
    )
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_ov", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 2
    assert records[0].originHostname == "root-backend.example.com"
    assert records[1].originHostname == "child-backend.example.com"


def test_extract_rule_records_no_origin_anywhere_emits_nothing(client):
    """A rule tree with no origin behaviors at any level emits zero records."""
    child = _make_rule("v1-api", criteria=[_path_criterion(["/v1/*"])])
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_noop", propertyName="p", version=1, deeplink=""
    )
    assert records == []


# ── extractOutboundPath ────────────────────────────────────────────────────────


def _rewrite_behavior(mode, **opts):
    return {"name": "rewriteUrl", "options": {"behavior": mode, **opts}}


def _base_directory_behavior(value):
    return {"name": "baseDirectory", "options": {"value": value}}


def test_extract_outbound_path_no_rewrite_behaviors(client):
    behaviors = [_origin_behavior()]
    outbound_path, base_dir = client.extractOutboundPath(behaviors)
    assert outbound_path is None
    assert base_dir is None


def test_extract_outbound_path_rewrite_url_replace(client):
    behaviors = [_rewrite_behavior("REPLACE", match="/legacy/", targetPath="/new/")]
    outbound_path, base_dir = client.extractOutboundPath(behaviors)
    assert outbound_path == "REPLACE:/legacy/→/new/"
    assert base_dir is None


def test_extract_outbound_path_rewrite_url_remove(client):
    behaviors = [_rewrite_behavior("REMOVE", match="/api/")]
    outbound_path, _ = client.extractOutboundPath(behaviors)
    assert outbound_path == "REMOVE:/api/"


def test_extract_outbound_path_rewrite_url_rewrite(client):
    behaviors = [_rewrite_behavior("REWRITE", targetUrl="/internal/page.html")]
    outbound_path, _ = client.extractOutboundPath(behaviors)
    assert outbound_path == "REWRITE:/internal/page.html"


def test_extract_outbound_path_rewrite_url_prepend(client):
    behaviors = [_rewrite_behavior("PREPEND", targetPathPrepend="/v3")]
    outbound_path, _ = client.extractOutboundPath(behaviors)
    assert outbound_path == "PREPEND:/v3"


def test_extract_outbound_path_rewrite_url_regex_replace(client):
    behaviors = [
        _rewrite_behavior(
            "REGEX_REPLACE", matchRegex="^/api/(.*)", targetRegex="/v3/api/$1"
        )
    ]
    outbound_path, _ = client.extractOutboundPath(behaviors)
    assert outbound_path == "REGEX:^/api/(.*)→/v3/api/$1"


def test_extract_outbound_path_base_directory(client):
    behaviors = [_base_directory_behavior("/images/")]
    outbound_path, base_dir = client.extractOutboundPath(behaviors)
    assert outbound_path is None
    assert base_dir == "/images/"


def test_extract_outbound_path_both_rewrite_and_basedir(client):
    behaviors = [
        _rewrite_behavior("PREPEND", targetPathPrepend="/v3"),
        _base_directory_behavior("/static/"),
    ]
    outbound_path, base_dir = client.extractOutboundPath(behaviors)
    assert outbound_path == "PREPEND:/v3"
    assert base_dir == "/static/"


def test_extract_rule_records_outbound_path_on_record(client):
    """rewriteUrl behavior is captured on the emitted record."""
    child = _make_rule(
        "v1",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[
            _origin_behavior(),
            _rewrite_behavior("PREPEND", targetPathPrepend="/internal"),
        ],
    )
    root = _make_rule("default", children=[child])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_rw", propertyName="p", version=1, deeplink=""
    )
    assert len(records) == 1
    assert records[0].outboundPath == "PREPEND:/internal"
    assert records[0].baseDirectory is None


def test_extract_rule_records_outbound_path_inherited(client):
    """Child without its own rewriteUrl inherits parent's outbound_path."""
    grandchild = _make_rule(
        "grandchild",
        criteria=[_path_criterion(["/v1/users/*"])],
        behaviors=[_origin_behavior("gc-backend.example.com")],
    )
    parent = _make_rule(
        "v1",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[
            _origin_behavior(),
            _rewrite_behavior("PREPEND", targetPathPrepend="/internal"),
        ],
        children=[grandchild],
    )
    root = _make_rule("default", children=[parent])
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_rw2", propertyName="p", version=1, deeplink=""
    )
    # parent: 1 record (path="/v1/*")
    # grandchild: 1 record (path="/v1/* AND /v1/users/*")
    assert len(records) == 2
    for r in records:
        assert r.outboundPath == "PREPEND:/internal"  # all carry it


def test_extract_rule_records_outbound_path_child_overrides(client):
    """Child's own rewriteUrl overrides the inherited one."""
    child = _make_rule(
        "v1",
        criteria=[_path_criterion(["/v1/*"])],
        behaviors=[
            _origin_behavior(),
            _rewrite_behavior("REWRITE", targetUrl="/new-path"),
        ],
    )
    root = _make_rule(
        "default",
        behaviors=[
            _origin_behavior("root-backend.example.com"),
            _rewrite_behavior("PREPEND", targetPathPrepend="/v3"),
        ],
        children=[child],
    )
    records = client.extractRuleRecords(
        rule=root, propertyId="prp_rw3", propertyName="p", version=1, deeplink=""
    )
    # root: path=None, child: path="/v1/*"
    assert len(records) == 2
    root_record = next(r for r in records if r.path is None)
    child_record = next(r for r in records if r.path == "/v1/*")
    assert root_record.outboundPath == "PREPEND:/v3"
    assert child_record.outboundPath == "REWRITE:/new-path"
