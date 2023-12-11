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
    cloudlet_policies: dict
    hostnames: List[EdgeHost]

    @property
    def origin_count(self):
        return len(self.origins)

    @property
    def hostname_count(self):
        return len(self.hostnames)

    @property
    def cloudlet_policy_count(self):
        return {"edgeRedirector": len(self.cloudlet_policies["edgeRedirector"])}

    def as_eventbus_json(self):
        return {
            "id": f"akamai_property:{self.id}",
            "name": self.name,
            "version": self.version,
            "origin_count": self.origin_count,
            "cloudlet_policy_count": self.cloudlet_policy_count,
            "hostname_count": self.hostname_count,
            "origins": [{"name": origin.name} for origin in self.origins],
            "cloudlet_policies": {
                "edgeRedirector": [
                    {"policyId": policyId}
                    for policyId in self.cloudlet_policies["edgeRedirector"]
                ],
            },
            "hostnames": [{"name": hostname.name} for hostname in self.hostnames],
        }
