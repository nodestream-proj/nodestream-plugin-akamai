import pytest
import responses

from nodestream_akamai.akamai_utils.client import (
    AkamaiApiClient,
    AkamaiAuthenticationError,
)


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
    responses.add(rsp1)
    responses.add(rsp1)
    responses.add(
        method="GET",
        url="https://fake.example.com/example",
        status=200,
        json={"key": "value"},
    )

    assert client._get_api_from_relative_path("example") == {"key": "value"}


@responses.activate
def test_401_get_response_with_body(client):
    """Test that 401 responses immediately fail with response body information."""
    error_body = '{"error": "Invalid credentials", "code": "AUTH_ERROR"}'
    responses.add(
        method="GET",
        url="https://fake.example.com/example",
        status=401,
        body=error_body,
    )

    with pytest.raises(AkamaiAuthenticationError) as exc_info:
        client._get_api_from_relative_path("example")

    # Check that the exception contains the response body
    assert "Authentication failed for 'GET https://fake.example.com/example'" in str(
        exc_info.value
    )
    assert error_body in str(exc_info.value)
    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 401


@responses.activate
def test_401_get_response_without_body(client):
    """Test that 401 responses immediately fail even without response body."""
    rsp = responses.Response(
        method="GET",
        url="https://fake.example.com/example",
        status=401,
    )
    responses.add(rsp)

    with pytest.raises(AkamaiAuthenticationError) as exc_info:
        client._get_api_from_relative_path("example")

    # Check that the exception contains the expected message
    assert "Authentication failed for 'GET https://fake.example.com/example'" in str(
        exc_info.value
    )
    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 401


@responses.activate
def test_401_post_response_without_body(client):
    """Test that 401 responses immediately fail even without response body."""
    responses.add(
        method="POST",
        url="https://fake.example.com/example",
        status=401,
    )

    with pytest.raises(AkamaiAuthenticationError) as exc_info:
        client._post_api_from_relative_path("example", {})

    # Check that the exception contains the expected message
    assert "Authentication failed for 'POST https://fake.example.com/example'" in str(
        exc_info.value
    )
    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 401


@responses.activate
def test_401_post_response_with_body(client):
    """Test that 401 responses immediately fail for POST requests with response body information."""
    error_body = '{"error": "Invalid credentials", "code": "AUTH_ERROR"}'
    rsp = responses.Response(
        method="POST",
        url="https://fake.example.com/example",
        status=401,
        body=error_body,
    )
    responses.add(rsp)

    with pytest.raises(AkamaiAuthenticationError) as exc_info:
        client._post_api_from_relative_path("example", {"test": "data"})

    # Check that the exception contains the response body
    assert "Authentication failed for 'POST https://fake.example.com/example'" in str(
        exc_info.value
    )
    assert error_body in str(exc_info.value)
    assert exc_info.value.response is not None
    assert exc_info.value.response.status_code == 401
