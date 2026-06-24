from dataclasses import dataclass, field
from typing import List, Optional


DEEPLINK_BASE = "https://control.akamai.com/apps/property-manager/#/property-version"


@dataclass(kw_only=True)
class AkamaiPropertyResponse:
    propertyId: str
    propertyName: str
    productionVersion: Optional[int]
    stagingVersion: Optional[int]
    assetId: str
    contractId: str
    groupId: str
    hostnames: List[dict]

    @property
    def deeplink(self) -> str:
        return (
            f"{DEEPLINK_BASE}/{self.assetId}/{self.productionVersion}/edit"
            f"?gid={self.groupId}"
        )

    @classmethod
    def fromDict(cls, data: dict) -> "AkamaiPropertyResponse":
        return cls(
            propertyId=data["propertyId"],
            propertyName=data["propertyName"],
            productionVersion=data.get("productionVersion"),
            stagingVersion=data.get("stagingVersion"),
            assetId=data.get("assetId", ""),
            contractId=data.get("contractId", ""),
            groupId=data.get("groupId", ""),
            hostnames=data.get("hostnames", []),
        )


@dataclass(eq=True, frozen=True, kw_only=True)
class EdgeHost:
    name: str


@dataclass(eq=True, frozen=True, kw_only=True)
class Origin:
    name: str
    path: str | None = None
    hostname: str | None = None
    conditional_origin: str | None = None


@dataclass(kw_only=True)
class PropertyDescription:
    id: str
    name: str
    hostnames: List[EdgeHost]
    version: str | None = None
    origins: List[Origin] = field(default_factory=list)
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

    def dict_factory(
        self,
    ):  # pragma: no cover  # unused; extractor calls dataclasses.asdict
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
            "hostnames": self.hostnames,
        }


@dataclass(kw_only=True)
class PropertyRuleRecord:
    """One rule node flattened for pipeline consumption.

    Mirrors RouteRecord in the service registry extractor — one record per
    rule node that has an origin behavior (or is the default/root rule).

    Key design for micromatch compatibility
    ----------------------------------------
    pathCriteria is stored as List[str] where each element is a single glob
    pattern, possibly !-prefixed for negation.  This maps directly to the
    micromatch(path, patterns) call signature — no post-hoc parsing required.

    The node key ``path`` is the sorted pathCriteria list joined with " AND "
    so that each unique combination of criteria maps to exactly one Path node,
    regardless of rule tree traversal order.  One rule → one Path node; no
    fan-out per positive glob.

    Path label eligibility (by design)
    ------------------------------------
    A rule gets the ``Path`` label (via pathKey being non-null) iff:
      - pathCriteria is non-empty
      - conditionalOriginId is None
    Hostname-dimensioned rules are still path-eligible — the hostname just
    scopes inbound traffic; the path glob is a genuine allowlist entry.
    """

    # Node key fields (match IAGE Path key structure)
    proxyId: str  # = propertyId (the AkamaiProperty node key value)
    path: Optional[
        str
    ]  # sorted pathCriteria joined with AND; None when not path-eligible

    # Properties surfaced on the node
    pathCriteria: List[str]  # individual glob patterns for micromatch
    hostnameCriteria: List[str]  # hostname match values (separate dimension)
    conditionalOriginId: Optional[str]

    # Origin routing (populates ROUTES_TO)
    originHostname: Optional[str]
    originType: Optional[str]  # "CUSTOMER" | "NET_STORAGE" | "MEDIA_SERVICE_LIVE"

    # Outbound path rewriting (rewriteUrl / baseDirectory behaviors)
    outboundPath: Optional[
        str
    ]  # The rewritten path forwarded to origin; None = same as inbound
    baseDirectory: Optional[
        str
    ]  # baseDirectory prefix prepended unconditionally; None = no prefix

    # Rule metadata
    ruleName: str
    ruleDepth: int  # 0 = default/root rule
    criteriaMustSatisfy: str  # "all" | "any"
    securityBehaviors: List[str]  # e.g. ["AKAMAI_EDGE_AUTH"]

    # Property context (carried for pipeline pass 1 keying)
    propertyId: str
    propertyName: str
    version: int
    deeplink: str
