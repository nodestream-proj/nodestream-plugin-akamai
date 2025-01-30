"""Common utils for getting information about addresses."""
from enum import StrEnum
from ipaddress import IPv4Address, IPv6Address, ip_address


class AddressNodeType(StrEnum):
    CIDRIPV4 = "Cidripv4"
    CIDRIPV6 = "Cidripv6"
    ENDPOINT = "Endpoint"


class AddressFormat(StrEnum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    ENDPOINT = "endpoint"
    INVALID = "Invalid"

    @property
    def node_type(self) -> AddressNodeType:
        """Get the node type for this kind of address"""
        return ADDRESS_FORMAT_TO_NODE_TYPE.get(self)


ADDRESS_FORMAT_TO_NODE_TYPE = {
    AddressFormat.IPV4: AddressNodeType.CIDRIPV4,
    AddressFormat.IPV6: AddressNodeType.CIDRIPV6,
    AddressFormat.ENDPOINT: AddressNodeType.ENDPOINT,
}


def get_format(address: int | str | bytes | IPv4Address | IPv6Address) -> AddressFormat:
    """Figure out the format type of the address"""
    try:
        ip_addr = ip_address(address)
    except ValueError:
        ip_addr = address

    match ip_addr:
        case IPv4Address():
            return AddressFormat.IPV4
        case IPv6Address():
            return AddressFormat.IPV6
        case other if " " in other:
            return AddressFormat.INVALID
        case _:
            return AddressFormat.ENDPOINT
