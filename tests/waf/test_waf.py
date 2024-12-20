import pytest

from nodestream_akamai.waf import waf


@pytest.fixture
def waf_extractor():
    return waf.AkamaiWafExtractor(
        base_url="https://fake.example.com",
        client_token="ctoken",
        client_secret="secret",
        access_token="atoken",
        max_retries=5,
        retry_wait_seconds_min=0,
        retry_wait_seconds_max=0,
    )


def test_extract_policy(waf_extractor):
    assert waf_extractor.extract_policy(
        {
            "id": "test-policy-id",
            "name": "test-policy-name",
            "webApplicationFirewall": {
                "attackGroupActions": [
                    {
                        "group": "XSS",
                        "action": "test-action-XSS",
                    },
                    {
                        "group": "LFI",
                        "action": "test-action-LFI",
                    },
                ]
            },
        }
    ) == {
        "policyId": "test-policy-id",
        "policyName": "test-policy-name",
        "attackGroupActions": [
            {
                "action": "test-action-XSS",
                "group": "XSS",
                "groupName": "Cross Site Scripting",
            },
            {
                "action": "test-action-LFI",
                "group": "LFI",
                "groupName": "Local File Inclusion",
            },
        ],
    }


test_groups = [(ag, ag.title) for ag in waf.ActionGroup]


@pytest.mark.parametrize("group_name, expected_group_name", test_groups)
def test_extract_attack_group_action(waf_extractor, group_name, expected_group_name):
    assert waf_extractor.extract_attack_group_action(
        {
            "group": group_name,
            "action": "test-action",
        }
    ) == {
        "group": group_name,
        "groupName": expected_group_name,
        "action": "test-action",
    }
