import pytest
import requests
import responses

import nodestream_akamai.akamai_utils.client as client


@responses.activate
def test_get():
    rsp1 = responses.Response(
        responses.GET,
        "https://fake.example.com/example",
        status=requests.codes.internal_server_error,
        json={"error": "message500"},
    )
    rsp2 = responses.Response(
        responses.GET,
        "https://fake.example.com/example",
        status=requests.codes.not_implemented,
        json={"error": "message503"},
    )
    rsp3 = responses.Response(
        responses.GET,
        "https://fake.example.com/example",
        status=requests.codes.created,
        json={"message": "created"},
    )
    responses.add(rsp1)
    responses.add(rsp2)
    responses.add(rsp3)

    c = client.AkamaiApiClient(
        "https://fake.example.com",
        "client_token",
        "client_secret",
        "access_token",
        retry_wait_seconds_min=0,
        retry_wait_seconds_max=0,
    )

    with pytest.raises(client.AkamaiClientException) as e:
        c._get_api_from_relative_path("/example")
    assert str(e.value) == "response.status_code: 201"
    assert e.value.text == '{"message": "created"}'

    # the first 2 are handled via the request internal Retry pattern for 5xx responses
    assert rsp1.call_count == 1
    assert rsp2.call_count == 1
    # the last 1 counts as a success with the wrong kind of status_code
    assert rsp3.call_count == 4
