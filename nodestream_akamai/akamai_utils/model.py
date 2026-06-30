from dataclasses import dataclass, field
from typing import List, Optional

# Akamai/PAPI-facing records intentionally keep API-shaped field names.
# Pipeline YAML maps those emitted keys to graph snake_case properties.


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
class AkamaiPropertyResponse:
    """Typed representation of a single PAPI property response item.

    Populated from the raw dict returned by list_account_hostnames /
    get_property so that downstream code works with attributes instead
    of string-keyed dict access.
    """

    propertyId: str
    propertyName: str
    productionVersion: Optional[int]
    stagingVersion: Optional[int] = None
    assetId: Optional[str] = None
    contractId: Optional[str] = None
    groupId: Optional[str] = None
    hostnames: List[dict] = field(default_factory=list)

    @classmethod
    def fromDict(cls, raw: dict) -> "AkamaiPropertyResponse":
        return cls(
            propertyId=raw["propertyId"],
            propertyName=raw["propertyName"],
            productionVersion=raw.get("productionVersion"),
            stagingVersion=raw.get("stagingVersion"),
            assetId=raw.get("assetId"),
            contractId=raw.get("contractId"),
            groupId=raw.get("groupId"),
            hostnames=raw.get("hostnames", []),
        )

    @property
    def deeplink(self) -> str:
        return (
            "https://control.akamai.com/apps/property-manager/"
            f"#/property-version/{self.assetId}/{self.productionVersion}/edit"
            f"?gid={self.groupId}"
        )


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
    # Output field stays API-shaped; YAML maps it onto graph property rule_path.
    rulePath: str  # JSON Pointer path in the rule tree, e.g. /rules/children/0
    ruleName: str
    ruleDepth: int  # 0 = default/root rule
    criteriaMustSatisfy: str  # "all" | "any"
    securityBehaviors: List[str]  # e.g. ["AKAMAI_EDGE_AUTH"]

    # Property context (carried for pipeline pass 1 keying)
    propertyId: str
    propertyName: str
    version: int
    deeplink: str
