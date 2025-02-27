import pytest

from nodestream_akamai.akamai_utils import Origin
from nodestream_akamai.akamai_utils.property_client import AkamaiPropertyClient
from tests.akamai_utils.rulesdata import rule_tree_488011, rule_tree_643957

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


def test_search_akamai_rule_tree_for_origins_simple(client):
    assert client.search_akamai_rule_tree_for_origins(CRITERIA_RULE["rules"]) == {
        Origin("example.com")
    }


def test_search_akamai_rule_tree_for_origins(client):

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
    assert client.search_akamai_rule_tree_for_origins(rule_tree) == {
        Origin(name="customer-hostname"),
        Origin(name="mslorigin"),
        Origin(name="netstorage-downloaddomainname"),
    }


def test_collate_origins_with_criteria(client):
    rules = CRITERIA_RULE
    result = client.collate_origins_with_criteria(rules)

    assert result == [Origin(name="example.com")]


def test_collate_live(client):
    assert client.collate_origins_with_criteria(rule_tree_643957["rules"]) == [
        Origin(name="community.example.com"),
        Origin(name="sgds.download.akamai.com"),
        Origin(name="sitemap-cdn.example.com"),
        Origin(name="sitemap-cdn.example.com"),
        Origin(name="dcgfr56345.stage.lithium.com"),
        Origin(name="sh-exp-sgds.example.com"),
        Origin(name="example-render.example.com"),
        Origin(name="example-render.example.com"),
        Origin(name="example-render.example.com"),
    ]
    assert client.collate_origins_with_criteria(rule_tree_488011["rules"]) == [
        Origin(name="example.download.akamai.com")
    ]


def test_live_search_akamai_rule_tree_for_cloudlets(client):
    assert client.search_akamai_rule_tree_for_cloudlets(rule_tree_488011["rules"]) == []
    assert client.search_akamai_rule_tree_for_cloudlets(rule_tree_643957["rules"]) == [
        32773,
        116717,
    ]


def test_live_search_akamai_rule_tree_for_cloudlet(client):
    assert (
        client.search_akamai_rule_tree_for_cloudlet(
            rule_tree_488011["rules"],
            behavior_name="edgeRedirector",
            shared=False,
        )
        == []
    )
    assert client.search_akamai_rule_tree_for_cloudlet(
        rule_tree_643957["rules"],
        behavior_name="edgeRedirector",
        shared=False,
    ) == [116717]


def test_live_search_akamai_rule_tree_for_ivm(client):
    assert client.search_akamai_rule_tree_for_ivm(rule_tree_488011) == []
    assert client.search_akamai_rule_tree_for_ivm(rule_tree_643957) == []


def test_live_search_akamai_rule_tree_for_edge_workers(client):
    assert (
        client.search_akamai_rule_tree_for_edge_workers(rule_tree_488011["rules"]) == []
    )
    assert (
        client.search_akamai_rule_tree_for_edge_workers(rule_tree_643957["rules"]) == []
    )


def test_live_search_akamai_rule_tree_for_siteshield(client):
    assert (
        client.search_akamai_rule_tree_for_siteshield(rule_tree_488011["rules"]) == []
    )
    assert client.search_akamai_rule_tree_for_siteshield(rule_tree_643957["rules"]) == [
        "s2604.akamaiedge.net"
    ]


def test_live_search_akamai_rule_tree_for_cp_codes(client):
    assert client.search_akamai_rule_tree_for_cp_codes(rule_tree_488011["rules"]) == [
        640994
    ]
    assert client.search_akamai_rule_tree_for_cp_codes(rule_tree_643957["rules"]) == [
        752101
    ]
