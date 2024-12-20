import pytest
import responses

from nodestream_akamai.cloudlets import cloudlets
from nodestream_akamai.cloudlets.cloudlets import PolicyType


@pytest.fixture
def cloudlet_extractor():
    return cloudlets.AkamaiCloudletExtractor(
        base_url="https://fake.example.com",
        client_token="ctoken",
        client_secret="secret",
        access_token="atoken",
        retry_wait_seconds_min=0,
        retry_wait_seconds_max=0,
    )


def test_enhance_policy_v3_no_activations(cloudlet_extractor):
    assert cloudlet_extractor.enhance_policy_v3(
        {
            "cloudletType": "CD",
            "id": "test-id",
        },
        "test-deeplink",
    ) == {
        "activeProductionVersion": None,
        "activeStagingVersion": None,
        "cloudletType": "CD",
        "deeplink": "test-deeplink",
        "id": "test-id",
        "isShared": True,
        "policyId": "test-id",
        "policyType": "Phased Release",
    }


def test_enhance_policy_v3_only_staging(cloudlet_extractor):
    assert cloudlet_extractor.enhance_policy_v3(
        {
            "cloudletType": "CD",
            "currentActivations": {
                "staging": {"effective": {"policyVersion": "test-version-1"}},
            },
            "id": "test-id",
        },
        "test-deeplink",
    ) == {
        "activeProductionVersion": None,
        "activeStagingVersion": "test-version-1",
        "cloudletType": "CD",
        "currentActivations": {
            "staging": {"effective": {"policyVersion": "test-version-1"}},
        },
        "deeplink": "test-deeplink",
        "id": "test-id",
        "isShared": True,
        "policyId": "test-id",
        "policyType": "Phased Release",
    }


def test_enhance_policy_v3_only_prod(cloudlet_extractor):
    assert cloudlet_extractor.enhance_policy_v3(
        {
            "cloudletType": "CD",
            "currentActivations": {
                "production": {"effective": {"policyVersion": "test-version-2"}},
            },
            "id": "test-id",
        },
        "test-deeplink",
    ) == {
        "activeProductionVersion": "test-version-2",
        "activeStagingVersion": None,
        "cloudletType": "CD",
        "currentActivations": {
            "production": {"effective": {"policyVersion": "test-version-2"}}
        },
        "deeplink": "test-deeplink",
        "id": "test-id",
        "isShared": True,
        "policyId": "test-id",
        "policyType": "Phased Release",
    }


def test_enhance_policy_v3_both(cloudlet_extractor):
    assert cloudlet_extractor.enhance_policy_v3(
        {
            "cloudletType": "CD",
            "currentActivations": {
                "production": {"effective": {"policyVersion": "test-version-2"}},
                "staging": {"effective": {"policyVersion": "test-version-1"}},
            },
            "id": "test-id",
        },
        "test-deeplink",
    ) == {
        "activeProductionVersion": "test-version-2",
        "cloudletType": "CD",
        "currentActivations": {
            "production": {"effective": {"policyVersion": "test-version-2"}},
            "staging": {"effective": {"policyVersion": "test-version-1"}},
        },
        "deeplink": "test-deeplink",
        "id": "test-id",
        "isShared": True,
        "policyId": "test-id",
        "policyType": "Phased Release",
        "activeStagingVersion": "test-version-1",
    }


@pytest.mark.parametrize("policy_type", PolicyType)
def test_enhance_policy_v3_all_types(cloudlet_extractor, policy_type):
    assert cloudlet_extractor.enhance_policy_v3(
        {
            "cloudletType": str(policy_type),
            "id": "test-id",
        },
        "test-deeplink",
    ) == {
        "activeProductionVersion": None,
        "activeStagingVersion": None,
        "cloudletType": policy_type,
        "deeplink": "test-deeplink",
        "id": "test-id",
        "isShared": True,
        "policyId": "test-id",
        "policyType": policy_type.title,
    }


@pytest.mark.parametrize("policy_type", PolicyType)
def test_enhance_policy_v2_all_types(cloudlet_extractor, policy_type):
    assert cloudlet_extractor.enhance_policy_v2(
        {
            "cloudletCode": str(policy_type),
            "policyId": "test-id",
            "groupId": "test-group-2",
            "activations": [],
        },
        "test-deeplink",
    ) == {
        "activations": [],
        "cloudletCode": policy_type,
        "deeplink": "test-deeplink",
        "groupId": "test-group-2",
        "isShared": False,
        "policyId": "test-id",
        "policyType": policy_type.title,
    }


def test_enhance_policy_v2_both_activations(cloudlet_extractor):
    assert cloudlet_extractor.enhance_policy_v2(
        {
            "cloudletCode": "FR",
            "policyId": "test-id",
            "groupId": "test-group-2",
            "activations": [
                {"network": "prod", "policyInfo": {"version": "v1"}},
                {"network": "staging", "policyInfo": {"version": "v2"}},
            ],
        },
        "test-deeplink",
    ) == {
        "activations": [
            {"network": "prod", "policyInfo": {"version": "v1"}},
            {"network": "staging", "policyInfo": {"version": "v2"}},
        ],
        "activeProductionVersion": "v1",
        "activeStagingVersion": "v2",
        "cloudletCode": "FR",
        "deeplink": "test-deeplink",
        "groupId": "test-group-2",
        "isShared": False,
        "policyId": "test-id",
        "policyType": "Forward Rewrite",
    }


@responses.activate
@pytest.mark.asyncio
async def test_extract_records(cloudlet_extractor):
    rsp1 = responses.get(
        url="https://fake.example.com/cloudlets/v3/policies?size=9999",
        json={
            "content": [
                {
                    "cloudletType": "AS",
                    "id": "test-id-1",
                    "groupId": "test-group-1",
                },
            ]
        },
    )
    rsp2 = responses.get(
        url="https://fake.example.com/cloudlets/api/v2/policies?offset=0",
        json=[
            {
                "cloudletCode": "AS",
                "policyId": "test-id-2",
                "groupId": "test-group-2",
                "activations": [],
            },
        ],
    )
    responses.add(rsp1)
    responses.add(rsp2)

    records = []
    async for record in cloudlet_extractor.extract_records():
        records.append(record)
    records = sorted(records, key=lambda r: r["policyId"])
    assert records == [
        {
            "activeProductionVersion": None,
            "activeStagingVersion": None,
            "cloudletType": "AS",
            "deeplink": "https://control.akamai.com/apps/cloudlets/#/policies/test-id-1/versions?gid=test-group-1&shared=true",
            "groupId": "test-group-1",
            "id": "test-id-1",
            "isShared": True,
            "policyId": "test-id-1",
            "policyType": "Audience Segmentation",
        },
        {
            "activations": [],
            "cloudletCode": "AS",
            "deeplink": "https://control.akamai.com/apps/cloudlets/#/policies/test-id-2/versions?gid=test-group-2&shared=false",
            "groupId": "test-group-2",
            "isShared": False,
            "policyId": "test-id-2",
            "policyType": "Audience Segmentation",
        },
    ]
