from unittest.mock import Mock

import pytest

from nodestream_akamai.akamai_utils import Origin
from nodestream_akamai.akamai_utils.property_client import AkamaiPropertyClient
from tests.akamai_utils.rulesdata import (
    rule_tree_488011,
    rule_tree_627844,
    rule_tree_643957,
)

# Test names mirror the legacy camelCase client methods they cover.

CRITERIA_RULE = {
    "rules": {
        "name": "default",
        "options": {"is_secure": False},
        "behaviors": [
            {
                "name": "origin",
                "options": {
                    "originType": "CUSTOMER",
                    "hostname": "example.com",
                    "forwardHostHeader": "REQUEST_HOST_HEADER",
                    "cacheKeyHostname": "ORIGIN_HOSTNAME",
                    "compress": True,
                    "tcipEnabled": False,
                    "httpPort": 80,
                },
            },
            {
                "name": "cpCode",
                "options": {"value": {"id": 12345, "name": "main site"}},
            },
        ],
        "children": [
            {
                "name": "Compress Text Content",
                "criteria": [
                    {
                        "name": "contentType",
                        "options": {
                            "matchOperator": "IS_ONE_OF",
                            "matchWildcard": True,
                            "matchCaseSensitive": False,
                            "values": [
                                "text/html*",
                                "text/css*",
                                "application/x-javascript*",
                            ],
                        },
                    }
                ],
                "behaviors": [
                    {"name": "gzipResponse", "options": {"behavior": "ALWAYS"}}
                ],
            }
        ],
    }
}


@pytest.fixture
def client():
    return AkamaiPropertyClient(
        base_url="url",
        client_token="ctoken",
        client_secret="client",
        access_token="atoken",
    )


def test_searchRuleTreeForOrigins_simple(client):
    assert client.searchRuleTreeForOrigins(CRITERIA_RULE["rules"]) == {
        Origin(name="example.com")
    }


def test_list_all_properties_propagates_hostname_errors(client):
    client.listAccountHostnames = Mock(side_effect=RuntimeError("bad base url"))

    with pytest.raises(RuntimeError, match="bad base url"):
        client.list_all_properties()


def test_searchRuleTreeForOrigins(client):

    rule_tree = {
        "behaviors": [
            {
                "name": "origin",
                "options": {"originType": "CUSTOMER", "hostname": "customer-hostname"},
            },
            {
                "name": "origin",
                "options": {
                    "originType": "NET_STORAGE",
                    "netStorage": {
                        "downloadDomainName": "netstorage-downloaddomainname"
                    },
                },
            },
            {
                "name": "origin",
                "options": {
                    "originType": "MEDIA_SERVICE_LIVE",
                    "mslorigin": "mslorigin",
                },
            },
            {"name": "other"},
        ],
        "children": [
            {
                "behaviors": [
                    {
                        "name": "origin",
                        "options": {
                            "originType": "CUSTOMER",
                            "hostname": "customer-hostname",
                        },
                    },
                ],
                "children": [],
            },
            {"behaviors": [], "children": []},
        ],
    }
    assert client.searchRuleTreeForOrigins(rule_tree) == {
        Origin(name="customer-hostname"),
        Origin(name="mslorigin"),
        Origin(name="netstorage-downloaddomainname"),
    }


def test_collateOriginsWithCriteria(client):
    rules = CRITERIA_RULE
    result = client.collateOriginsWithCriteria(rules)

    assert result == [Origin(name="example.com")]


def test_collate_live_643957(client):
    assert client.collateOriginsWithCriteria(rule_tree_643957["rules"]) == [
        Origin(name="c.example.com"),
        Origin(name="sgds.download.akamai.com"),
        Origin(name="s.example.com", path="/community/sitemap*.xml"),
        Origin(name="s.example.com", path="/robots.txt"),
        Origin(
            name="dcgfr56345.stage.lithium.com",
            path="/community AND !/community/sitemap*.xml",
        ),
        Origin(
            name="dcgfr56345.stage.lithium.com",
            path="/community/* AND !/community/sitemap*.xml",
        ),
        Origin(name="s.example.com", path="/example-support"),
        Origin(name="s.example.com", path="/example-support/en-us"),
        Origin(name="s.example.com", path="/example-support/en-us/*"),
        Origin(name="s.example.com", path="/example-support/"),
        Origin(name="s.example.com", path="/example-support/es-us"),
        Origin(name="s.example.com", path="/example-support/es-us/*"),
        Origin(name="e.example.com", path="/community AND !/community/*/amp"),
        Origin(name="e.example.com", path="/community AND !/community/sitemap*.xml"),
        Origin(name="e.example.com", path="/community AND !/community/*/help/*/00/*"),
        Origin(name="e.example.com", path="/community AND !/community/*/help/*/01/*"),
        Origin(name="e.example.com", path="/community/* AND !/community/*/amp"),
        Origin(name="e.example.com", path="/community/* AND !/community/sitemap*.xml"),
        Origin(name="e.example.com", path="/community/* AND !/community/*/help/*/00/*"),
        Origin(name="e.example.com", path="/community/* AND !/community/*/help/*/01/*"),
        Origin(name="e.example.com"),
        Origin(name="e.example.com"),
    ]


def test_collate_live_488011(client):
    assert client.collateOriginsWithCriteria(rule_tree_488011["rules"]) == [
        Origin(name="example.download.akamai.com")
    ]


def test_collate_live_627844(client):
    assert client.collateOriginsWithCriteria(rule_tree_627844["rules"]) == [
        Origin(name="w.example.com"),
        Origin(
            name="www.mczbf.com",
            path="/proxydirectory/*",
        ),
        Origin(name="examplegpm.download.akamai.com", path="/robots.txt"),
        Origin(
            name="examplegpm.download.akamai.com",
            path="/googlef2feb1480d7429b5.html",
        ),
        Origin(name="examplegpm.download.akamai.com", path="/sitemap.xml"),
        Origin(name="example.download.akamai.com", path="/file/*"),
        Origin(name="example.download.akamai.com", hostname="t.example.ca"),
        Origin(name="r.example.com", path="/_next/*"),
        Origin(name="r.example.com", path="/gwp-components/*"),
        Origin(name="r.example.com", path="/gwp-cg-components/*"),
        Origin(name="r.example.com", hostname="t.example.ca"),
        Origin(name="w.example.com"),
        Origin(name="w.example.com"),
        Origin(name="examplegpm.download.akamai.com", conditional_origin="MAINTENANCE"),
        Origin(name="p.example.ca", conditional_origin="dc1_impot_ca_prod"),
        Origin(name="c.example.com", conditional_origin="contentmesh"),
    ]


def test_live_searchRuleTreeForCloudlets(client):
    assert client.searchRuleTreeForCloudlets(rule_tree_488011["rules"]) == []
    assert client.searchRuleTreeForCloudlets(rule_tree_643957["rules"]) == [
        32773,
        116717,
    ]


def test_live_searchRuleTreeForCloudlet(client):
    assert (
        client.searchRuleTreeForCloudlet(
            rule_tree_488011["rules"],
            behaviorName="edgeRedirector",
            shared=False,
        )
        == []
    )
    assert client.searchRuleTreeForCloudlet(
        rule_tree_643957["rules"],
        behaviorName="edgeRedirector",
        shared=False,
    ) == [116717]


def test_live_searchRuleTreeForIvm(client):
    assert client.searchRuleTreeForIvm(rule_tree_488011) == []
    assert client.searchRuleTreeForIvm(rule_tree_643957) == []


def test_live_searchRuleTreeForEdgeWorkers(client):
    assert client.searchRuleTreeForEdgeWorkers(rule_tree_488011["rules"]) == []
    assert client.searchRuleTreeForEdgeWorkers(rule_tree_643957["rules"]) == []


def test_live_searchRuleTreeForSiteshield(client):
    assert client.searchRuleTreeForSiteshield(rule_tree_488011["rules"]) == []
    assert client.searchRuleTreeForSiteshield(rule_tree_643957["rules"]) == [
        "s2604.akamaiedge.net"
    ]


def test_live_searchRuleTreeForCpCodes(client):
    assert client.searchRuleTreeForCpCodes(rule_tree_488011["rules"]) == [640994]
    assert client.searchRuleTreeForCpCodes(rule_tree_643957["rules"]) == [752101]
