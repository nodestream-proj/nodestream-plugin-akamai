from dataclasses import dataclass, field
from typing import List


@dataclass(eq=True, frozen=True)
class EdgeHost:
    name: str


@dataclass(eq=True, frozen=True)
class Origin:
    name: str
    path: str | None = None
    hostname: str | None = None
    conditional_origin: str | None = None


@dataclass
class PropertyDescription:
    id: str
    name: str
    origins: List[Origin]
    hostnames: List[EdgeHost]
    version: str | None = None
    siteshield_maps: List[str] = field(default_factory=list)
    rule_format: str | None = None
    image_manager_policysets: List[str] = field(default_factory=list)
    edgeworker_ids: List[int] = field(default_factory=list)
    edge_redirector_policies: List[int] = field(default_factory=list)
    deeplink: str | None = None
    cloudlet_policies: List[int] = field(default_factory=list)
    cp_codes: List[int] = field(default_factory=list)

    @property
    def origin_count(self):
        return len(self.origins)

    @property
    def hostname_count(self):
        return len(self.hostnames)

    def as_eventbus_json(self):
        return {
            "id": f"akamai_property:{self.id}",
            "name": self.name,
            "version": self.version,
            "ruleFormat": self.rule_format,
            "origin_count": self.origin_count,
            "cloudlet_policy_count": len(self.cloudlet_policies),
            "hostname_count": self.hostname_count,
            "origins": self.origins,
            "cloudlet_policies": self.cloudlet_policies,
            "edge_redirector_policies": self.edge_redirector_policies,
            "edgeworker_ids": self.edgeworker_ids,
            "siteshield_maps": self.siteshield_maps,
            "image_manager_policysets": self.image_manager_policysets,
            "hostnames": [
                {"name": hostname["cnameFrom"]} for hostname in self.hostnames
            ],
        }
