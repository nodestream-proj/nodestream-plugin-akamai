import asyncio
from typing import AsyncGenerator

import pytest
import responses

from nodestream_akamai.edns import edns


@pytest.fixture
def edns_extractor():
    return edns.AkamaiEdnsExtractor(
        base_url="https://fake.example.com",
        client_token="ctoken",
        client_secret="secret",
        access_token="atoken",
    )


async def to_list_async(generator: AsyncGenerator):
    output = []
    async for record in generator:
        output.append(record)
    return output


@responses.activate
def test_extract_records(edns_extractor):
    """Happy path check"""
    rsp1 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones?showAll=true",
        status=200,
        json={
            "zones": [
                {
                    "zone": "test-zone-1",
                },
                {
                    "zone": "test-zone-2",
                },
            ]
        },
    )
    responses.add(rsp1)

    rsp2 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones/test-zone-1/recordsets?showAll=true",
        status=200,
        json={
            "recordsets": [
                {
                    "name": "rs-1",
                    "type": "PRIMARY",
                    "rdata": ["Not", "Going", "To", "Make", "It"],
                },
                {"name": "rs-2", "type": "CNAME", "rdata": ["Hello"]},
                {"name": "rs-3", "type": "A", "rdata": ["192.168.1.1"]},
            ]
        },
    )
    responses.add(rsp2)

    rsp3 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones/test-zone-2/recordsets?showAll=true",
        status=200,
        json={
            "recordsets": [
                {
                    "name": "rs-4",
                    "type": "AAAA",
                    "rdata": [
                        "3271:9297:1824:7ed9:9f9d:3535:4b3c:8274",
                        "dce8:a12b:d609:f7d8:fb8c:2b68:68d4:bf6b",
                    ],
                },
                {"name": "rs-5", "type": "CNAME", "rdata": ["Goodbye"]},
                {"name": "rs-6", "type": "A", "rdata": ["192.168.1.2"]},
            ]
        },
    )
    responses.add(rsp3)

    result = asyncio.run(to_list_async(edns_extractor.extract_records()))
    assert result == [
        {
            "recordsets": [
                {
                    "Endpoint": ["Hello"],
                    "key": "rs-2/CNAME",
                    "name": "rs-2",
                    "rdata": ["Hello"],
                    "type": "CNAME",
                    "zone": "test-zone-1",
                },
                {
                    "Cidripv4": ["192.168.1.1"],
                    "key": "rs-3/A",
                    "name": "rs-3",
                    "rdata": ["192.168.1.1"],
                    "type": "A",
                    "zone": "test-zone-1",
                },
            ],
            "zone": "test-zone-1",
        },
        {
            "recordsets": [
                {
                    "Cidripv6": [
                        "3271:9297:1824:7ed9:9f9d:3535:4b3c:8274",
                        "dce8:a12b:d609:f7d8:fb8c:2b68:68d4:bf6b",
                    ],
                    "key": "rs-4/AAAA",
                    "name": "rs-4",
                    "rdata": [
                        "3271:9297:1824:7ed9:9f9d:3535:4b3c:8274",
                        "dce8:a12b:d609:f7d8:fb8c:2b68:68d4:bf6b",
                    ],
                    "type": "AAAA",
                    "zone": "test-zone-2",
                },
                {
                    "Endpoint": ["Goodbye"],
                    "key": "rs-5/CNAME",
                    "name": "rs-5",
                    "rdata": ["Goodbye"],
                    "type": "CNAME",
                    "zone": "test-zone-2",
                },
                {
                    "Cidripv4": ["192.168.1.2"],
                    "key": "rs-6/A",
                    "name": "rs-6",
                    "rdata": ["192.168.1.2"],
                    "type": "A",
                    "zone": "test-zone-2",
                },
            ],
            "zone": "test-zone-2",
        },
    ]


@responses.activate
def test_extract_records_zone_fetch_fail(edns_extractor):
    rsp1 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones?showAll=true",
        status=400,
    )
    responses.add(rsp1)

    with pytest.raises(Exception):
        asyncio.run(to_list_async(edns_extractor.extract_records()))


@responses.activate
def test_extract_records_recordsets_fetch_fail(edns_extractor):
    rsp1 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones?showAll=true",
        status=200,
        json={
            "zones": [
                {
                    "zone": "test-zone-error",
                }
            ]
        },
    )
    responses.add(rsp1)
    rsp2 = responses.Response(
        method="GET",
        url="https://fake.example.com/config-dns/v2/zones/test-zone-error/recordsets?showAll=true",
        status=400,
    )
    responses.add(rsp2)
    with pytest.raises(Exception):
        asyncio.run(to_list_async(edns_extractor.extract_records()))
