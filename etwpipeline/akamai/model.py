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
    version: str
    origins: List[Origin]
    edge_redirector_policies: List[str]
    hostnames: List[EdgeHost]

    @property
    def origin_count(self):
        return len(self.origins)

    @property
    def hostname_count(self):
        return len(self.hostnames)
    
    @property
    def edge_redirector_count(self):
        return len(self.edge_redirector_policies)

    def as_eventbus_json(self):
        return {
            "id": f"akamai_property:{self.id}",
            "name": self.name,
            "version": self.version,
            "origin_count": self.origin_count,
            "edge_redirector_count": self.edge_redirector_count,
            "hostname_count": self.hostname_count,
            "origins": [{"name": origin.name} for origin in self.origins],
            "edge_redirector_policies": [{"policyId": policyId} for policyId in self.edge_redirector_policies],
            "hostnames": [{"name": hostname.name} for hostname in self.hostnames],
        }
