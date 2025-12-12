from unittest.mock import MagicMock, Mock

import pytest
from requests import HTTPError

from nodestream_akamai import AkamaiStagingPropertyExtractor
from nodestream_akamai.akamai_utils.model import PropertyDescription


@pytest.fixture
def extractor():
    extractor = AkamaiStagingPropertyExtractor(
        base_url="test_url",
        client_token="test_client_token",
        client_secret="test_client_secret",
        access_token="test_access_token",
    )
    extractor.client = MagicMock()
    return extractor


@pytest.mark.asyncio
async def test_extract_records_fail_list_props(extractor):
    extractor.client.list_all_properties = Mock(
        side_effect=HTTPError("expected test error")
    )
    with pytest.raises(HTTPError):
        _ignore = [x async for x in extractor.extract_records()]


@pytest.mark.asyncio
async def test_extract_records_fail_other(extractor):
    extractor.client.list_all_properties = Mock(
        return_value=[
            {},
            {
                "stagingVersion": "test",
                "propertyName": "test-name",
                "propertyId": "1234",
            },
        ]
    )
    extractor.client.describe_property_by_dict = Mock(side_effect=KeyError)

    assert [x async for x in extractor.extract_records()] == []


@pytest.mark.asyncio
async def test_extract_records_success(extractor):
    mock_property = {
        "stagingVersion": 42,
        "propertyName": "test-property",
        "propertyId": "prp_123",
        "contractId": "ctr_123",
        "groupId": "grp_123",
        "assetId": "aid_123",
    }

    mock_description = PropertyDescription(
        id="prp_123",
        name="test-property",
        origins=[],
        hostnames=[],
    )

    extractor.client.list_all_properties = Mock(return_value=[mock_property])
    extractor.client.describe_property_by_dict = Mock(return_value=mock_description)

    results = [x async for x in extractor.extract_records()]

    assert len(results) == 1
    extractor.client.describe_property_by_dict.assert_called_once_with(
        prop=mock_property, version=42
    )
