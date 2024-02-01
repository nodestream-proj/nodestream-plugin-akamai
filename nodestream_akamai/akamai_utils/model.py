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
    cloudlet_policies: List[int]
    edge_redirector_policies: List[int]
    edgeworker_ids: List[int]
    siteshield_maps: List[str]
    image_manager_policysets: List[str]
    hostnames: List[EdgeHost]
    ruleFormat: str

    @property
    def origin_count(self):
        return len(self.origins)

    @property
    def hostname_count(self):
        return len(self.hostnames)

    # @property
    # def cloudlet_policy_count(self):
    #     return {"edgeRedirector": len(self.cloudlet_policies["edgeRedirector"])}

    def as_eventbus_json(self):
        return {
            "id": f"akamai_property:{self.id}",
            "name": self.name,
            "version": self.version,
            "ruleFormat": self.ruleFormat,
            "origin_count": self.origin_count,
            "cloudlet_policy_count": len(self.cloudlet_policies),
            "hostname_count": self.hostname_count,
            "origins": [{"name": origin.name} for origin in self.origins],
            "cloudlet_policies": self.cloudlet_policies,
            "edge_redirector_policies": self.edge_redirector_policies,
            "edgeworker_ids": self.edgeworker_ids,
            "siteshield_maps": self.siteshield_maps,
            "image_manager_policysets": self.image_manager_policysets,
            "hostnames": [{"name": hostname.name} for hostname in self.hostnames],
        }
