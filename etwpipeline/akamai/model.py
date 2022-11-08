from dataclasses import dataclass
from typing import List


@dataclass(eq=True, frozen=True)
class EdgeHost:
    name: str


@dataclass(eq=True, frozen=True)
class Origin:
    name: str


@dataclass
class PropertyDescription:
    id: str
    name: str
    origins: List[Origin]
    edge_hosts: List[EdgeHost]

    @property
    def origin_count(self):
        return len(self.origins)

    @property
    def edge_host_count(self):
        return len(self.edge_hosts)

    def as_eventbus_json(self):
        return {
            "id": f"akamai_property:{self.id}",
            "name": self.name,
            "origin_count": self.origin_count,
            "edge_host_count": self.edge_host_count,
            "edge_hosts": [{"name": edge_host.name} for edge_host in self.edge_hosts],
            "origins": [{"name": origin.name} for origin in self.origins],
        }
