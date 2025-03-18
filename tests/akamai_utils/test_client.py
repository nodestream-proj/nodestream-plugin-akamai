import pytest
import responses

from nodestream_akamai.akamai_utils.client import AkamaiApiClient


@pytest.fixture
def client():
    client = AkamaiApiClient(
        base_url="https://fake.example.com",
        client_token="ctoken",
        client_secret="secret",
        access_token="atoken",
    )
    client.backoff_delays = [0, 0, 0, 0, 0]
    return client


@responses.activate
def test_429_get_response(client):
    rsp1 = responses.Response(
        method="GET",
        url="https://fake.example.com/example",
        status=429,
    )
    rsp2 = responses.Response(
        method="GET",
        url="https://fake.example.com/example",
        status=200,
        json={"key": "value"},
    )
    responses.add(rsp1)
    responses.add(rsp1)
    responses.add(rsp2)

    assert client._get_api_from_relative_path("example") == {"key": "value"}
