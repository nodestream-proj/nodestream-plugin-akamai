"""Tests for model.py dataclasses."""

from nodestream_akamai.akamai_utils.model import EdgeHost, Origin, PropertyDescription


def _make_property_description(origins=None, hostnames=None):
    return PropertyDescription(
        id="prp_1",
        name="test-property",
        hostnames=hostnames or [],
        origins=origins or [],
    )


def test_property_description_origin_count():
    origins = [
        Origin(name="o1", hostname="backend1.example.com"),
        Origin(name="o2", hostname="backend2.example.com"),
    ]
    prop = _make_property_description(origins=origins)
    assert prop.origin_count == 2


def test_property_description_origin_count_empty():
    prop = _make_property_description(origins=[])
    assert prop.origin_count == 0


def test_property_description_hostname_count():
    hostnames = [EdgeHost(name="ehn1.example.com"), EdgeHost(name="ehn2.example.com")]
    prop = _make_property_description(hostnames=hostnames)
    assert prop.hostname_count == 2


def test_property_description_hostname_count_empty():
    prop = _make_property_description(hostnames=[])
    assert prop.hostname_count == 0
