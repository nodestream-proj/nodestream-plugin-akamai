from unittest.mock import MagicMock, Mock

import pytest
from requests import HTTPError

from nodestream_akamai import AkamaiPropertyExtractor
from nodestream_akamai.akamai_utils.model import AkamaiPropertyResponse


@pytest.fixture
def extractor():
    extractor = AkamaiPropertyExtractor(
        base_url="test_url",
        client_token="test_client_token",
        client_secret="test_client_secret",
        access_token="test_access_token",
    )
    extractor.client = MagicMock()
    return extractor


def _make_prop(**kwargs):
    defaults = {
        "propertyId": "prp_1234",
        "propertyName": "test-name",
        "productionVersion": 1,
        "stagingVersion": None,
        "assetId": "aid_1",
        "contractId": "ctr_1",
        "groupId": "grp_1",
        "hostnames": [],
    }
    defaults.update(kwargs)
    return AkamaiPropertyResponse(**defaults)


@pytest.mark.asyncio
async def test_extract_records_fail_list_props(extractor):
    extractor.client.list_all_properties = Mock(side_effect=HTTPError("test error"))
    with pytest.raises(HTTPError):
        _ignore = [x async for x in extractor.extract_records()]


@pytest.mark.asyncio
async def test_extract_records_fail_other(extractor):
    extractor.client.list_all_properties = Mock(
        return_value=[
            None,
            _make_prop(
                productionVersion=1, propertyName="test-name", propertyId="1234"
            ),
        ]
    )
    extractor.client.describePropertyByDict = Mock(side_effect=KeyError)

    assert [x async for x in extractor.extract_records()] == []
