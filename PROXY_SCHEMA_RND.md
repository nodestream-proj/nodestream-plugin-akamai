# Proxy Schema R&D: Adapting the IntuitApiGatewayEnvironment Proxy Pattern to AkamaiProperty

**Date:** 2026-06-15
**Author:** Research synthesized from codebase exploration
**Scope:** nodestream-plugin-akamai at `/Users/asantos4/Documents/nodestream-plugin-akamai`, reference implementation at `/Users/asantos4/Documents/endpoint-graph-ingest`

---

## Executive Summary

**Feasibility: HIGH** — the adaptation is architecturally sound and the data required is already being extracted (rule tree traversal is already in production). The primary effort is in:
1. Adding a new `AkamaiPropertyRule` node type (the Path equivalent)
2. Extending the extractor to emit per-rule records (currently only property-level records are emitted)
3. Adding 5 new interpretation passes to the property pipeline YAML
4. Writing 2 migration files

**Confidence: MEDIUM-HIGH** — the analogy between Akamai's rule-tree model and the Services Registry route model is architecturally clean. The key uncertainties are: (a) the criteria-matching logic is lossy (it drops negative-match contexts), (b) origin fan-out is very high (a single property may have 5–20+ rule-origin combos), and (c) auth/security behavior mapping requires new extraction logic that doesn't exist today.

**What this unlocks in the graph:**
- Path-level routing intelligence: which Akamai rule routes which hostname patterns to which origin
- Per-rule security posture: which rules have WAF, which have SiteShield, which have EdgeAuth token validation
- Origin attribution: implicit ownership signal for origin hostnames
- A traversal pattern `(Endpoint)-[:SERVICED_BY]->(AkamaiProperty)-[:HAS_RULE]->(AkamaiPropertyRule)-[:ROUTES_TO]->(Endpoint)` that mirrors the service registry pattern exactly

---

## Section 1: Reference Proxy Schema

### 1.1 The Pipeline Structure

The reference implementation is in `pipelines/crons/services-registry-ingest.yaml` with extractor logic in `munchlax/extractors/service_registry_extractor.py`.

The pipeline runs **5 interpretation passes** over each flattened `RouteRecord` (one record per endpoint × route × target combination):

**Pass 1 — Proxy node creation with top-level relationships:**
- Source node: `IntuitApiGatewayEnvironment` (labels: `[IntuitApiGatewayEnvironment, Proxy]`, key: `id`)
- Properties: `name`, `environment_name`, `hosting`
- Relationships:
  - `OWNED_BY` → `Asset` (via `asset_id`)
  - `USES_AUTHENTICATION_POLICY` → `AuthenticationPolicy` (via `auth_protocols[*]`, find_many)
  - `GRANTS_AUTHORIZATION_TO` → `OauthParty` (via `oauth_application_types[*]`, find_many)
  - `EXPOSES_DATA_WITH_CLASSIFICATION` → `DataClassification` (via `oauth_data_sensitivities[*]`, find_many)
  - `SERVICED_BY` (inbound) ← `Endpoint` (via `cnames[*]`, find_many) — the "front-door" FQDNs the proxy answers on

**Pass 2 — Endpoint as source:**
- Source node: `Endpoint` (key: `fqdn = endpoint_fqdn`)
- Relationship: `SERVICED_BY` → `IntuitApiGatewayEnvironment` (the canonical endpoint FQDN's upward link to its proxy)

**Pass 3 — Proxy → Path + PROXIES_TO (coarse backend link):**
- Source node: `IntuitApiGatewayEnvironment` (same key)
- Relationship: `HAS_PATH` → `Path` (key: `proxy_id + path_inbound`), with `path_outbound` as node property and `route_name` on the relationship
- Relationship: `PROXIES_TO` → `Endpoint` (key: `target_dns`, find_many) — the set of backend endpoints this proxy can forward to

**Pass 4 — Path as source → ROUTES_TO backend Endpoint:**
- Source node: `Path` (key: `proxy_id + path_inbound`)
- Relationship: `ROUTES_TO` → `Endpoint` (key: `target_dns`)
  - Relationship properties: `target_name`, `target_raw_dns`, `target_mesh_dns`, `target_workload_env_selector`

**Pass 5 — Backend Endpoint → IMPLICITLY_OWNED_BY Asset:**
- Source node: `Endpoint` (key: `target_dns`)
- Relationship: `IMPLICITLY_OWNED_BY` → `Asset` (MATCH_ONLY, key: `normalized_asset_alias`)

### 1.2 The Domain Model

The extractor flattens the hierarchical service config into flat `RouteRecord` objects, one per endpoint × route × target combination:

```python
@dataclass
class RouteRecord:
    asset_id: str               # owning asset
    endpoint_fqdn: str          # the canonical "front door" FQDN
    cnames: List[str]           # additional CNAMEs this endpoint answers on
    apigw_env_id: str           # stable ID for the Proxy node
    path_inbound: Optional[str] # the inbound path pattern (e.g. "/v1/identity/*")
    path_outbound: Optional[str]# the rewritten outbound path (if any)
    route_name: Optional[str]
    target_dns: Optional[str]   # resolved backend FQDN
    target_asset_alias: Optional[str]  # inferred asset alias for IMPLICITLY_OWNED_BY
    target_name: Optional[str]
    target_raw_dns: Optional[str]
    target_mesh_dns: Optional[str]
    target_workload_env_selector: Optional[str]
```

### 1.3 Schema Summary (Node/Relationship Types)

| Node Type | Key | Notes |
|---|---|---|
| `IntuitApiGatewayEnvironment` (+ `Proxy`) | `id` | The proxy/gateway config |
| `Path` | `proxy_id + path` | One per inbound route path |
| `Endpoint` | `fqdn` | Both frontend and backend |
| `AuthenticationPolicy` | `name` | Auth protocol names |
| `Asset` | `normalized_asset_alias` | Owning asset |

| Relationship | From → To | Notes |
|---|---|---|
| `OWNED_BY` | Proxy → Asset | Explicit from config |
| `USES_AUTHENTICATION_POLICY` | Proxy → AuthenticationPolicy | Auth protocol from filter |
| `SERVICED_BY` | Endpoint → Proxy | Front-door CNAME/FQDN |
| `HAS_PATH` | Proxy → Path | route_name on rel |
| `PROXIES_TO` | Proxy → Endpoint | Coarse backend (de-duped) |
| `ROUTES_TO` | Path → Endpoint | Fine-grained per-path backend |
| `IMPLICITLY_OWNED_BY` | Endpoint → Asset | Inferred from mesh FQDN |

---

## Section 2: Akamai Data Inventory

### 2.1 What the Plugin Extracts Today

The plugin is organized as independent pipeline YAML files, each with its own extractor:

#### `property.yaml` / `AkamaiPropertyExtractor`

Calls `list_all_properties()` which:
1. Lists all account hostnames via `/papi/v1/hostnames?network=PRODUCTION`
2. De-dupes by `propertyId`
3. For each property with a production version, calls `describe_property_by_dict(prop, version=productionVersion)` which:
   - Calls `/papi/v1/properties/{id}/versions/{version}/rules` (the **full rule tree**)
   - Extracts origins via `collate_origins_with_criteria(rules)` — this already traverses the full rule tree and collects criteria
   - Extracts cloudlet_policies, edge_redirector_policies, image_manager_policysets, edgeworker_ids, siteshield_maps, cp_codes

**Emitted `PropertyDescription` dict per property:**
```python
{
    "id": "akamai_property:{propertyId}",
    "name": str,
    "version": int,
    "ruleFormat": str,
    "origins": [Origin(name, path, hostname, conditional_origin)],
    "hostnames": [EdgeHost(name)],  # cnameFrom values
    "cloudlet_policies": [int],
    "edge_redirector_policies": [int],
    "image_manager_policysets": [str],
    "edgeworker_ids": [int],
    "siteshield_maps": [str],
    "cp_codes": [int],
    "deeplink": str,
}
```

**Current graph interpretations (property.yaml):**
- `AkamaiProperty` node (key: `id`)
- Properties: `name`, `version`, `rule_format`, `deeplink`
- `SERVICED_BY` (inbound) ← `Endpoint` (via `hostnames[*].name`, find_many) — the front-door FQDNs
- `PROXIES_TO` → `Endpoint` (via `origins[*].name`, iterate_on) — the backend origins
  - Relationship properties: `path`, `hostname`, `conditional_origin` (from the `Origin` dataclass)
  - Node property: `type: origin`
- `MEDIA_OPTIMIZED_BY` → `AkamaiIvmPolicySet`
- `OFFLOADS_CONFIGURATION_TO` → `AkamaiCloudlet`
- `RUNS_CODE_FOR` (inbound) ← `AkamaiEdgeworker`
- `ROUTES_THROUGH` → `AkamaiSiteshieldMap`
- `REDIRECTS_IN` → `AkamaiRedirectConfig`
- `REPORTS_ON` (inbound) ← `AkamaiCPCode`

#### `appsec-coverage.yaml` / `AkamaiAppSecCoverageExtractor`

Links `AkamaiWafPolicy` → `Endpoint` via `PROTECTED_BY`.

#### `waf.yaml` / `AkamaiWafExtractor`

Creates `AkamaiWafConfig` and `AkamaiWafPolicy` nodes with attack group actions.

#### `ehn.yaml` / `AkamaiEhnExtractor`

Creates `AkamaiEdgeHostname` nodes and links to `Endpoint` via `CNAMES_TO`.

#### `gtm.yaml` / `AkamaiGtmExtractor`

Creates `AkamaiGtmProperty` → `Endpoint`, `Cidripv4`, `Cidripv6` via `RESOLVES_TO`.

#### `cloudlets.yaml` / `AkamaiCloudletExtractor`

Creates `AkamaiCloudlet` nodes (independent of property pipeline).

#### `cps.yaml` / `AkamaiCpsExtractor`

Creates `AkamaiCertificate` → `Endpoint` via `ENCRYPTED_BY`.

#### `edns.yaml` / `AkamaiEdnsExtractor`

Creates `AkamaiEdnsZone` / `AkamaiEdnsRecordSet` → `Endpoint`, `Cidripv4`, `Cidripv6` via `RESOLVES_TO`.

#### Other pipelines

- `apidiscovery.yaml`: `AkamaiDiscoveredAPI` → `Endpoint` via `SERVICED_BY`
- `redirect.yaml`: `AkamaiRedirectConfig` → `Endpoint` via `REDIRECTS_HANDLED_BY` / `REDIRECTS_TO`
- `siteshield.yaml`: `AkamaiSiteshieldMap` → `Cidripv4` via `EGRESS`
- `ivm.yaml`: `AkamaiIvmPolicySet` nodes
- `cpcodes.yaml`: `AkamaiCPCode` nodes
- `iam-clients.yaml`, `iam-users.yaml`: IAM entities
- `staging-property.yaml`: mirrors property.yaml for `AkamaiStagingProperty`
- `netstorage-account.yaml`, `netstorage-group.yaml`: NetStorage entities

### 2.2 Key Data Already Available in the Rule Tree

The property extractor **already fetches the full rule tree** from the PAPI API. The rule tree is a recursive JSON structure:

```json
{
  "name": "default",
  "criteria": [],
  "behaviors": [
    {
      "name": "origin",
      "options": { "originType": "CUSTOMER", "hostname": "api.internal.example.com", "forwardHostHeader": "REQUEST_HOST_HEADER" }
    }
  ],
  "children": [
    {
      "name": "API Routes - /v1/payments",
      "criteria": [
        { "name": "path", "options": { "matchOperator": "MATCHES_ONE_OF", "values": ["/v1/payments", "/v1/payments/*"] } }
      ],
      "behaviors": [
        { "name": "origin", "options": { "originType": "CUSTOMER", "hostname": "payments-origin.internal.example.com" } },
        { "name": "siteShield", "options": { "ssmap": { "value": "s2604.akamaiedge.net" } } }
      ],
      "children": []
    }
  ]
}
```

**Data already being used:**
- `behaviors[name=origin].options.hostname` / `netStorage.downloadDomainName` / `mslorigin`
- Path criteria from `criteria[name=path].options.values`
- Hostname criteria from `criteria[name=hostname].options.values`
- `behaviors[name=siteShield]`
- `behaviors[name=cloudletPolicy/edgeRedirector/etc.]`
- `behaviors[name=imageManager/imageManagerVideo]`
- `behaviors[name=edgeWorker]`
- `behaviors[name=cpCode]`

**Data in the rule tree NOT currently extracted:**
- `children[*].name` — the human-readable rule name
- `children[*].criteria[name=path].options.values` — path match patterns (extracted but not stored per-rule)
- `children[*].criteria[name=hostname].options.values` — hostname match criteria
- `children[*].behaviors[name=caching]` — caching config (TTL, bypass rules)
- `children[*].behaviors[name=edgeAuth]` / `tokenAuth` — edge authentication behaviors
- `children[*].behaviors[name=sureRoute]` — SureRoute acceleration
- `children[*].behaviors[name=forwardRewrite]` — forward path rewrite
- `children[*].behaviors[name=modifyOutgoingRequestHeader]` — header manipulation
- `children[*].behaviors[name=allowPost]`, `allowDelete`, etc. — method allowlisting
- `children[*].criteriaMustSatisfy` — "all" vs "any" matching semantics
- `rule_name` — the `name` field on each rule node
- `comments` on rules

---

## Section 3: Ontological Analysis

### 3.1 Akamai in the Network Topology

An `AkamaiProperty` is a **CDN configuration** that sits between the internet and origin servers. Traffic flow:

```
Client → DNS → Edge Hostname (*.edgekey.net / *.akamai.net)
       → Akamai Edge Network → AkamaiProperty (rule matching)
       → Origin (by matched rule criteria)
```

This maps exactly to the Proxy pattern:
- The `AkamaiProperty` is the **Proxy** — it accepts traffic on multiple hostnames and routes to backends
- The `hostnames[*].cnameFrom` values are the **front-door FQDNs** (what clients use, what CNAMEs point to the edge hostname)
- The `origins[*].hostname` values are the **backend FQDNs** (where Akamai forwards to)
- The rule children with path/hostname criteria are the **Path** equivalent

### 3.2 Concept Mapping Table

| Services Registry Concept | Akamai Equivalent | Notes |
|---|---|---|
| `IntuitApiGatewayEnvironment` (Proxy) | `AkamaiProperty` | The configuration that accepts and routes traffic |
| `endpoint_fqdn` (front door) | `hostnames[*].cnameFrom` | The CNAMEs clients use (these CNAME to Akamai edge hostnames) |
| `cnames` (additional front doors) | Same `hostnames` list | Akamai has a flat list; all are "front doors" |
| `path_inbound` | Criteria in a rule child node | Path match values: e.g. `/api/v1/*` |
| `path_outbound` | `forwardRewrite` behavior options | Path rewriting, if present |
| `route_name` | Rule `name` field | Human name of the rule child node |
| `target_dns` | `origin.hostname` | The backend origin FQDN |
| `filter` → auth protocols | Security behaviors in the rule tree | `edgeAuth`, `tokenAuth`, WAF policy |
| `OWNED_BY` Asset | Not directly available | Would require groupId → contract → asset mapping |
| `USES_AUTHENTICATION_POLICY` | Rule-level auth behaviors | `edgeAuth`, `tokenAuth`, WAF policy ID |
| `SERVICED_BY` Endpoint | `hostnames[*]` → `AkamaiProperty` | Already implemented |
| `HAS_PATH` → Path | `AkamaiProperty` → `AkamaiPropertyRule` | New relationship, per-rule node |
| `PROXIES_TO` | `AkamaiProperty` → origin `Endpoint` | Already implemented |
| `ROUTES_TO` | `AkamaiPropertyRule` → origin `Endpoint` | New — per-rule routing link |

### 3.3 What AkamaiProperty Maps To vs. What AkamaiPropertyRule Maps To

**AkamaiProperty** maps to the **Proxy** label directly:
- It has a stable identity (`propertyId` / `id`)
- It controls which hostnames are served
- It has top-level behaviors (default origin, default WAF config, etc.)
- It owns the full configuration

**AkamaiPropertyRule** (new) maps to **Path**:
- It is a child rule in the rule tree
- It has matching criteria (path patterns, hostname patterns)
- It has behaviors that apply when the criteria match (specific origin, auth, caching)
- Its natural key is `(property_id, rule_path_pattern)` — see Section 5.2 for key design

### 3.4 The Auth Policy Equivalent

In the Services Registry model, a `Filter` has `authProtocols: ["OAUTH2_JWT", "API_KEY"]` etc., and these map to `AuthenticationPolicy` nodes. In Akamai, the analogues are:

1. **WAF Policy** — already modeled via `AkamaiWafPolicy` with `PROTECTED_BY` from `Endpoint`. This is the closest equivalent to a top-level "filter" applied per-hostname.

2. **`edgeAuth` behavior** — a behavior in the rule tree that requires a signed URL or token (Akamai EdgeAuth / EdgeAuth 2.0 / Token Auth 2.0). These appear as `behaviors[name="edgeAuth"]` or `behaviors[name="datastream2"]`. Example options:
   ```json
   { "name": "edgeAuth", "options": { "enabled": true, "algorithm": "SHA256", "parameterName": "token" } }
   ```

3. **`siteShield` behavior** — indicates that requests to origin must come through Akamai SiteShield egress CIDRs (mutual authentication at the network level). Already extracted into `AkamaiSiteshieldMap`.

4. **`allowPost`, `allowDelete` behavior** — restricts HTTP methods at the edge (a form of access control).

5. **`cloudletsOrigin` with `requestControl` cloudlet** — allows request filtering/blocking via an ALB-style cloudlet.

The closest 1-to-1 to `USES_AUTHENTICATION_POLICY` in the Akamai world is:
- `(AkamaiPropertyRule)-[:USES_AUTHENTICATION_BEHAVIOR]->(AkamaiSecurityBehavior)` where `AkamaiSecurityBehavior.name` is e.g. `"edgeAuth"`, `"tokenAuth"`, `"siteShield"`, or we reuse `AuthenticationPolicy` with names like `"AKAMAI_EDGE_AUTH"`.

**Recommended approach**: reuse `AuthenticationPolicy` (already exists) with behavior-derived names, matching the style of the Service Registry's `auth_protocols`. This keeps query patterns consistent.

### 3.5 Ownership Attribution

In the Service Registry model, ownership is explicit: `asset_id` comes from the service registry config, and `OWNED_BY` is a direct relationship.

In Akamai, there is no direct `assetId` field on a property. However:
- The property is associated with a `contractId` and `groupId`
- The `cpCode` (Cost and Profitability Code) is a billing/reporting unit that may map to an asset or team
- The `assetId` field is available on the rule tree response (`rule_tree["assetId"]`) — this is an Akamai internal asset ID, NOT a services-registry `asset_id`
- No direct bridge exists today between Akamai `propertyId` and Intuit `assetId`

**Gap**: Without a mapping table between Akamai properties and Intuit assets, `OWNED_BY` cannot be populated. This would require either:
- A curated mapping file (property name patterns → asset ID)
- An ACP attribute on the property group
- A shared tag/annotation in property names (e.g. properties named after their asset alias)

### 3.6 Multiple Paradigms Within AkamaiProperty

AkamaiProperty configurations span several paradigms:
1. **CDN caching** — most common behavior; rules optimize caching TTLs, compress, optimize media
2. **API gateway** — properties acting as an API gateway (path-based routing to multiple origins)
3. **Security filtering** — WAF, rate limiting via cloudlets, EdgeAuth
4. **Redirect handling** — via EdgeRedirector cloudlet (already modeled as `AkamaiRedirectConfig`)
5. **Load balancing** — via Application Load Balancer cloudlet (already modeled as `AkamaiCloudlet`)
6. **Media delivery** — IVM policies, NetStorage origins

For the Proxy schema, paradigms 1 and 2 are most relevant. The current extraction already handles most of the routing (origin extraction). The key addition is elevating per-rule routing to a named node type.

---

## Section 4: Gap Analysis

### 4.1 What Exists Today

| Capability | Status |
|---|---|
| Property node (`AkamaiProperty`) | Exists |
| Front-door FQDNs (`SERVICED_BY` ← Endpoint) | Exists |
| Backend origins (`PROXIES_TO` → Endpoint) | Exists |
| Origin with path criteria | Exists (path on PROXIES_TO relationship) |
| Origin with hostname criteria | Exists (hostname on PROXIES_TO relationship) |
| Conditional origin (cloudlet origin ID) | Exists (conditional_origin on PROXIES_TO) |
| Rule tree traversal | Exists (used by `collate_origins_with_criteria`) |
| SiteShield linkage | Exists |
| Cloudlet linkage | Exists |
| WAF policy linkage (via appsec-coverage) | Exists |
| EdgeWorker linkage | Exists |
| Rule **name** extraction | **Missing** |
| Per-rule node type (`AkamaiPropertyRule`) | **Missing** |
| Per-rule security behavior extraction | **Missing** |
| `OWNED_BY` Asset | **Missing** (no asset bridge) |
| `HAS_RULE` relationship (Proxy → Path equiv.) | **Missing** |
| `ROUTES_TO` relationship (Rule → Backend) | **Missing** |
| `USES_AUTHENTICATION_BEHAVIOR` per rule | **Missing** |
| `IMPLICITLY_OWNED_BY` for origin hostnames | **Missing** |

### 4.2 Data Available but Not Used

The rule tree is already fetched and parsed in full. The `collate_origins_with_criteria` method already traverses the tree and associates criteria with origins. The `rule_name` (from each `children[*].name`) is accessible during traversal but not stored.

The full set of behaviors per rule is accessible but only a subset is extracted globally (cloudlets, edgeworkers, siteshield, cpcode). Per-rule behavior classification is not done.

### 4.3 Data Not Available from Current API Calls

| Data | API to Add |
|---|---|
| Per-rule `edgeAuth` options | Already in rule tree, just not extracted |
| Per-rule `tokenAuth` options | Already in rule tree |
| Per-rule `sureRoute` options | Already in rule tree |
| Property group membership | `/papi/v1/groups` (already called in `contracts_by_group()`) |
| Hostname→property mapping for ownership | Would need external mapping or annotation |

### 4.4 Structural Challenges

**Fan-out problem:** A single `AkamaiProperty` may have:
- 1–50 frontend hostnames (`hostnames[*]`)
- 1–20 origin hostname/path combinations (`origins`)
- 3–30 rule children (in complex properties, 100+)

The current `property.yaml` pipeline emits **one record per property** and uses `find_many: true` and `iterate_on` to handle the lists. Adapting to a rule-level model requires emitting **one record per rule** within each property — a similar approach to how `RouteRecord` flattens routes.

**Criteria are aggregated, not per-rule today:** The `collate_origins_with_criteria` function aggregates path criteria from ALL rule levels into a combined string (e.g. `"/community AND !/community/sitemap*.xml"`). This is semantically accurate for origin resolution but doesn't directly give you "rule X has path criteria Y". We need to expose the rule-level breakdown in the extractor output.

**Negative criteria:** `DOES_NOT_MATCH_ONE_OF` and `IS_NOT_ONE_OF` are prefixed with `!` in the current extraction. These are valid match criteria but semantically complex for graph queries.

---

## Section 5: Proposed Design

### 5.1 Node Type: `AkamaiPropertyRule` (the Path equivalent)

This is the central new concept. It represents one rule node within an AkamaiProperty's rule tree.

**Definition:**

| Field | Type | Source | Notes |
|---|---|---|---|
| `property_id` (key) | string | `propertyId` | Stable property ID |
| `rule_path` (key) | string | JSONPath of rule in tree | e.g. `children.[0].children.[2]` — stable within a version |
| `rule_name` | string | `children[*].name` | Human name of the rule |
| `path_criteria` | string | criteria values, ANDed | e.g. `/api/v1/* AND !/api/v1/health` |
| `hostname_criteria` | string | criteria hostname values | e.g. `api.example.com AND !legacy.example.com` |
| `origin_name` | string | origin behavior hostname | The backend this rule forwards to |
| `criteria_must_satisfy` | string | `criteriaMustSatisfy` | `"all"` or `"any"` |
| `last_ingested_at` | datetime | nodestream | Standard TTL field |

**Key design decision:** The key must be stable across ingestion runs but unique per rule. Options:
1. `(property_id, rule_path)` where `rule_path` is the JSONPath position — stable if rule order doesn't change but brittle across rule reordering
2. `(property_id, rule_name)` — unstable if rule names change but human-readable
3. `(property_id, path_criteria)` — stable for path-based rules but collides when multiple rules match the same paths

**Recommended:** Use `(property_id, rule_name)` for human-readable keys, with a warning that duplicate rule names in a property will collide. For properties with unnamed rules, fall back to a hash of the criteria. This mirrors the `(proxy_id, path_inbound)` pattern in the reference implementation.

### 5.2 Relationship: `HAS_RULE` (Proxy → Path equiv.)

Replace the current `PROXIES_TO` coarse linkage with a two-level structure:

```
(AkamaiProperty)-[:HAS_RULE {rule_name}]->(AkamaiPropertyRule)
```

Relationship properties:
- `rule_name` — human-readable name (same as the node's `rule_name`, carried on the relationship for query convenience, mirroring `route_name` on `HAS_PATH`)

### 5.3 Relationship: `ROUTES_TO` (Path → Backend Endpoint)

```
(AkamaiPropertyRule)-[:ROUTES_TO]->(Endpoint {fqdn: origin_hostname})
```

Relationship properties:
- `origin_type` — `"CUSTOMER"`, `"NET_STORAGE"`, `"MEDIA_SERVICE_LIVE"`
- `path_criteria` — the inbound path match pattern
- `hostname_criteria` — the inbound hostname match pattern
- `conditional_origin_id` — if routing via an ALB cloudlet conditional origin

### 5.4 Relationship: `USES_AUTHENTICATION_BEHAVIOR`

```
(AkamaiPropertyRule)-[:USES_AUTHENTICATION_BEHAVIOR]->(AuthenticationPolicy)
```

Where `AuthenticationPolicy.name` is derived from the security behaviors found in the rule:
- `"AKAMAI_EDGE_AUTH"` — from `edgeAuth` behavior
- `"AKAMAI_TOKEN_AUTH"` — from `tokenAuth` behavior
- `"AKAMAI_SITE_SHIELD"` — from `siteShield` behavior (already modeled separately)
- `"AKAMAI_WAF"` — from WAF policy coverage (already available per-hostname via appsec-coverage)

This reuses the existing `AuthenticationPolicy` node type (already in schema) and makes cross-source security posture queries possible:
```cypher
MATCH (p:AuthenticationPolicy)<-[:USES_AUTHENTICATION_POLICY|USES_AUTHENTICATION_BEHAVIOR]-(n)
WHERE n:IntuitApiGatewayEnvironment OR n:AkamaiPropertyRule
RETURN p.name, collect(n)
```

### 5.5 Property Label on AkamaiProperty

Apply the `Proxy` additional label to `AkamaiProperty`, mirroring how `IntuitApiGatewayEnvironment` is also labeled `Proxy`:

```yaml
- type: source_node
  node_type: AkamaiProperty
  additional_types:
  - Proxy
```

This enables `MATCH (p:Proxy)` to return both IAGEs and AkamaiProperties.

### 5.6 `PROXIES_TO` Retained at Property Level

Keep the existing `PROXIES_TO` relationship from `AkamaiProperty` directly to backend `Endpoint` nodes. This is the coarse-grained routing link (equivalent to the IGW's direct `PROXIES_TO` in pass 3). The new `ROUTES_TO` via `AkamaiPropertyRule` adds fine-grained detail without removing the coarse link.

### 5.7 Confidence / Fan-out Heuristics

For properties with a single origin (common for dedicated service properties), `ROUTES_TO` confidence is high — there's only one backend. For properties with many rules and origins (large shared properties), each rule→origin link is a specific routing assertion, but the query patterns need to be aware that rule names can change across versions.

There is no need for a numeric `confidence` property on the relationships at this time. The presence of the relationship is deterministic from the rule tree. However, a `version` property on `AkamaiPropertyRule` (indicating which property version produced this rule) would help tracking.

---

## Section 6: Implementation Plan

### 6.1 New Extractor: `AkamaiPropertyRuleRecord`

Add a new dataclass to `nodestream_akamai/akamai_utils/model.py`:

```python
@dataclass(kw_only=True)
class PropertyRuleRecord:
    """One rule-to-origin mapping, flattened for pipeline consumption.

    Mirrors RouteRecord in the service registry extractor.
    One record per rule node that contains an origin behavior.
    """
    propertyId: str
    propertyName: str
    ruleName: str
    ruleDepth: int              # depth in tree (0 = default rule)
    pathCriteria: Optional[str] # ANDed path patterns, or None
    hostnameCriteria: Optional[str]
    conditionalOriginId: Optional[str]
    originHostname: Optional[str]
    originType: Optional[str]   # "CUSTOMER", "NET_STORAGE", "MEDIA_SERVICE_LIVE"
    securityBehaviors: List[str]  # e.g. ["AKAMAI_EDGE_AUTH", "AKAMAI_SITE_SHIELD"]
    criteriaMustSatisfy: str    # "all" or "any"
    version: int
    deeplink: str
```

### 6.2 New Extractor Method: `extract_rule_records`

Add to `AkamaiPropertyClient` in `nodestream_akamai/akamai_utils/property_client.py`:

```python
SECURITY_BEHAVIOR_MAP = {
    "edgeAuth": "AKAMAI_EDGE_AUTH",
    "tokenAuth": "AKAMAI_TOKEN_AUTH",
    "siteShield": "AKAMAI_SITE_SHIELD",
    "requestControl": "AKAMAI_REQUEST_CONTROL",
}

def extract_security_behaviors(self, behaviors: list) -> list[str]:
    """Return normalized security behavior names from a rule's behavior list."""
    result = []
    for behavior in behaviors:
        name = behavior.get("name", "")
        mapped = SECURITY_BEHAVIOR_MAP.get(name)
        if mapped and behavior.get("options", {}).get("enabled", True):
            result.append(mapped)
    return result

def extract_rule_records(
    self, rule, propertyId, propertyName, version, deeplink,
    depth=0, inherited_path_criteria=None, inherited_hostname_criteria=None
) -> list:
    """Recursively extract PropertyRuleRecord objects from the rule tree.

    Each rule node that contains an 'origin' behavior emits a record.
    Criteria from parent rules are ANDed with the current rule's criteria.
    """
    records = []

    # Extract criteria from this rule level
    path_values = []
    hostname_values = []
    for criterion in rule.get("criteria", []):
        if criterion["name"] == "path":
            vals = criterion["options"].get("values", [])
            op = criterion["options"].get("matchOperator", "")
            if op in NEGATIVE_OPERATORS:
                path_values.extend(f"!{v}" for v in vals)
            else:
                path_values.extend(vals)
        elif criterion["name"] == "hostname":
            vals = criterion["options"].get("values", [])
            op = criterion["options"].get("matchOperator", "")
            if op in NEGATIVE_OPERATORS:
                hostname_values.extend(f"!{v}" for v in vals)
            else:
                hostname_values.extend(vals)

    # Combine with inherited criteria (AND semantics)
    current_path = PATH_AND.join(filter(None, [inherited_path_criteria] + path_values)) or None
    current_hostname = PATH_AND.join(filter(None, [inherited_hostname_criteria] + hostname_values)) or None

    # Extract origin behavior if present
    origin = None
    for behavior in rule.get("behaviors", []):
        if behavior.get("name") == "origin":
            opts = behavior["options"]
            origin_type = opts.get("originType")
            if origin_type == "CUSTOMER":
                origin = (opts.get("hostname"), "CUSTOMER")
            elif origin_type == "NET_STORAGE":
                origin = (opts["netStorage"]["downloadDomainName"], "NET_STORAGE")
            elif origin_type == "MEDIA_SERVICE_LIVE":
                origin = (opts.get("mslorigin"), "MEDIA_SERVICE_LIVE")

    # Extract security behaviors
    security_behaviors = self.extract_security_behaviors(rule.get("behaviors", []))

    # Emit record if this rule has an origin behavior (or if it's the default rule with criteria)
    if origin is not None or (depth == 0 and any(rule.get("behaviors", []))):
        records.append(PropertyRuleRecord(
            propertyId=propertyId,
            propertyName=propertyName,
            ruleName=rule.get("name", "default"),
            ruleDepth=depth,
            pathCriteria=current_path,
            hostnameCriteria=current_hostname,
            conditionalOriginId=None,
            originHostname=origin[0] if origin else None,
            originType=origin[1] if origin else None,
            securityBehaviors=security_behaviors,
            criteriaMustSatisfy=rule.get("criteriaMustSatisfy", "all"),
            version=version,
            deeplink=deeplink,
        ))

    # Recurse into children
    for child in rule.get("children", []):
        records.extend(self.extract_rule_records(
            child, propertyId, propertyName, version, deeplink,
            depth=depth+1,
            inherited_path_criteria=current_path,
            inherited_hostname_criteria=current_hostname,
        ))

    return records
```

### 6.3 New Pipeline Extractor Class

Add `AkamaiPropertyRuleExtractor` to `nodestream_akamai/property_rule/__init__.py` and `property_rule/property_rule.py`:

```python
import dataclasses
import logging

from nodestream.pipeline.extractors import Extractor
from ..akamai_utils.property_client import AkamaiPropertyClient


class AkamaiPropertyRuleExtractor(Extractor):
    """Extracts per-rule records from AkamaiProperty rule trees.

    Emits one record per rule node that contains routing or security data.
    """
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiPropertyClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            properties = self.client.list_all_properties()
        except Exception as err:
            self.logger.exception("Failed to list properties: %s", err)
            raise err

        for prop in properties:
            if prop.get("productionVersion") is None:
                continue
            try:
                rule_tree = self.client.get_rule_tree(
                    property_id=prop["propertyId"],
                    version=prop["productionVersion"],
                    contract_id=prop["contractId"],
                    group_id=prop["groupId"],
                )
                deeplink_prefix = (
                    "https://control.akamai.com/apps/property-manager/#/property-version/"
                )
                deeplink = f'{deeplink_prefix}{prop["assetId"]}/{prop["productionVersion"]}/edit?gid={prop["groupId"]}'
                for record in self.client.extract_rule_records(
                    rule=rule_tree["rules"],
                    propertyId=prop["propertyId"],
                    propertyName=prop["propertyName"],
                    version=prop["productionVersion"],
                    deeplink=deeplink,
                ):
                    yield dataclasses.asdict(record)
            except Exception:
                self.logger.exception(
                    "Failed to extract rule records for property %s (id=%s)",
                    prop.get("propertyName"),
                    prop.get("propertyId"),
                )
```

### 6.4 New Pipeline YAML: `property-rule.yaml`

Create `nodestream_akamai/property-rule.yaml`:

```yaml
# AkamaiProperty Proxy Schema — rule-level pipeline
# Mirrors the 5-pass structure of services-registry-ingest.yaml
# Emits one record per rule node, enabling:
#   (Endpoint)-[:SERVICED_BY]->(AkamaiProperty:Proxy)-[:HAS_RULE]->(AkamaiPropertyRule)-[:ROUTES_TO]->(Endpoint)

- implementation: nodestream_akamai.property_rule:AkamaiPropertyRuleExtractor
  arguments:
    base_url: !config 'base_url'
    client_token: !config 'client_token'
    client_secret: !config 'client_secret'
    access_token: !config 'access_token'
    account_key: !config 'account_key'

- implementation: nodestream.interpreting:Interpreter
  arguments:
    interpretations:

    # Pass 1: AkamaiProperty as Proxy — apply Proxy label, link to front-door Endpoints
    # Note: front-door Endpoint linkage is already handled by property.yaml
    # This pass just ensures the Proxy label is present for cross-source queries
    - - type: source_node
        node_type: AkamaiProperty
        additional_types:
        - Proxy
        normalization:
          do_remove_trailing_dots: true
        key:
          id: !jmespath 'propertyId'
      - type: properties
        properties:
          name: !jmespath 'propertyName'
          version: !jmespath 'version'

    # Pass 2: AkamaiProperty -[HAS_RULE]-> AkamaiPropertyRule
    # Property as source, creating the rule node and linking it
    - - type: source_node
        node_type: AkamaiProperty
        additional_types:
        - Proxy
        normalization:
          do_remove_trailing_dots: true
        key:
          id: !jmespath 'propertyId'
      - type: relationship
        node_type: AkamaiPropertyRule
        relationship_type: HAS_RULE
        key_normalization:
          do_remove_trailing_dots: true
        node_key:
          property_id: !jmespath 'propertyId'
          rule_name: !jmespath 'ruleName'
        node_properties:
          path_criteria: !jmespath 'pathCriteria'
          hostname_criteria: !jmespath 'hostnameCriteria'
          criteria_must_satisfy: !jmespath 'criteriaMustSatisfy'
          origin_type: !jmespath 'originType'
          version: !jmespath 'version'
        relationship_properties:
          rule_name: !jmespath 'ruleName'

    # Pass 3: AkamaiPropertyRule -[ROUTES_TO]-> backend Endpoint
    # Rule as source, linking to origin Endpoint
    - - type: source_node
        node_type: AkamaiPropertyRule
        normalization:
          do_remove_trailing_dots: true
        key:
          property_id: !jmespath 'propertyId'
          rule_name: !jmespath 'ruleName'
      - type: relationship
        node_type: Endpoint
        relationship_type: ROUTES_TO
        node_creation_rule: EAGER
        key_normalization:
          do_remove_trailing_dots: true
        node_key:
          fqdn: !jmespath 'originHostname'
        relationship_properties:
          path_criteria: !jmespath 'pathCriteria'
          hostname_criteria: !jmespath 'hostnameCriteria'
          origin_type: !jmespath 'originType'
          conditional_origin_id: !jmespath 'conditionalOriginId'

    # Pass 4: AkamaiPropertyRule -[USES_AUTHENTICATION_BEHAVIOR]-> AuthenticationPolicy
    # Security behaviors discovered in the rule tree
    - - type: source_node
        node_type: AkamaiPropertyRule
        normalization:
          do_remove_trailing_dots: true
        key:
          property_id: !jmespath 'propertyId'
          rule_name: !jmespath 'ruleName'
      - type: relationship
        node_type: AuthenticationPolicy
        relationship_type: USES_AUTHENTICATION_BEHAVIOR
        key_normalization:
          do_remove_trailing_dots: true
        node_key:
          name: !jmespath 'securityBehaviors[*]'
        find_many: true

    # Pass 5: Endpoint as source — SERVICED_BY AkamaiProperty (Proxy)
    # Mirrors Pass 2 of services-registry-ingest: establishes the Endpoint->Proxy link
    # Note: this is already done in property.yaml for hostnames.
    # This pass is a no-op stub retained for structural parity — skip if property.yaml covers it.
```

### 6.5 Modify `property.yaml` — Add Proxy Label

Update the existing `property.yaml` to add the `Proxy` additional label:

```yaml
# In the source_node interpretation block, add:
- type: source_node
  node_type: AkamaiProperty
  additional_types:
  - Proxy          # <-- ADD THIS
  normalization:
    do_remove_trailing_dots: true
  key:
    id: !jmespath 'id'
```

### 6.6 Migration File: Create `AkamaiPropertyRule` node type

Create `migrations/20260615140000.yaml` in endpoint-graph-ingest:

```yaml
dependencies:
- '20260522175253'
name: '20260615140000'
operations:
# New node type: AkamaiPropertyRule (Path equivalent for Akamai)
- arguments:
    keys: !!set
      property_id: null
      rule_name: null
    name: AkamaiPropertyRule
    properties: !!set
      path_criteria: null
      hostname_criteria: null
      origin_type: null
      criteria_must_satisfy: null
      version: null
      last_ingested_at: null
  operation: CreateNodeType
- arguments:
    field_name: last_ingested_at
    node_type: AkamaiPropertyRule
  operation: AddAdditionalNodePropertyIndex

# HAS_RULE relationship (AkamaiProperty -> AkamaiPropertyRule)
- arguments:
    keys: !!set {}
    name: HAS_RULE
    properties: !!set
      rule_name: null
      last_ingested_at: null
  operation: CreateRelationshipType
- arguments:
    field_name: last_ingested_at
    relationship_type: HAS_RULE
  operation: AddAdditionalRelationshipPropertyIndex

# USES_AUTHENTICATION_BEHAVIOR relationship (AkamaiPropertyRule -> AuthenticationPolicy)
# AuthenticationPolicy node type already exists from services-registry schema
- arguments:
    keys: !!set {}
    name: USES_AUTHENTICATION_BEHAVIOR
    properties: !!set
      last_ingested_at: null
  operation: CreateRelationshipType
- arguments:
    field_name: last_ingested_at
    relationship_type: USES_AUTHENTICATION_BEHAVIOR
  operation: AddAdditionalRelationshipPropertyIndex

# Add Proxy label tracking: AkamaiProperty now also carries Proxy label
# (No schema change needed — the Proxy node type already exists as an abstract label)

# ROUTES_TO relationship already exists from services-registry schema
# Extend with new properties for Akamai-specific routing context
- arguments:
    default: null
    property_name: path_criteria
    relationship_type: ROUTES_TO
  operation: AddRelationshipProperty
- arguments:
    default: null
    property_name: hostname_criteria
    relationship_type: ROUTES_TO
  operation: AddRelationshipProperty
- arguments:
    default: null
    property_name: origin_type
    relationship_type: ROUTES_TO
  operation: AddRelationshipProperty
- arguments:
    default: null
    property_name: conditional_origin_id
    relationship_type: ROUTES_TO
  operation: AddRelationshipProperty
replaces: []
```

### 6.7 Example Cypher Queries Enabled by the New Schema

**1. Full routing path for a hostname:**
```cypher
MATCH (e:Endpoint {fqdn: "api.example.com"})-[:SERVICED_BY]->(p:AkamaiProperty)
OPTIONAL MATCH (p)-[:HAS_RULE]->(r:AkamaiPropertyRule)-[:ROUTES_TO]->(origin:Endpoint)
RETURN p.name, r.rule_name, r.path_criteria, origin.fqdn
ORDER BY r.rule_name
```

**2. All endpoints proxied through Akamai to a specific origin:**
```cypher
MATCH (frontend:Endpoint)-[:SERVICED_BY]->(p:AkamaiProperty)-[:HAS_RULE]->(r:AkamaiPropertyRule)-[:ROUTES_TO]->(origin:Endpoint {fqdn: "payments-api.internal.example.com"})
RETURN DISTINCT frontend.fqdn, p.name, r.rule_name, r.path_criteria
```

**3. Akamai properties with EdgeAuth protection (potential token auth coverage):**
```cypher
MATCH (r:AkamaiPropertyRule)-[:USES_AUTHENTICATION_BEHAVIOR]->(ap:AuthenticationPolicy)
WHERE ap.name = "AKAMAI_EDGE_AUTH"
MATCH (p:AkamaiProperty)-[:HAS_RULE]->(r)
OPTIONAL MATCH (e:Endpoint)-[:SERVICED_BY]->(p)
RETURN p.name, r.rule_name, r.path_criteria, collect(e.fqdn) AS front_door_fqdns
```

**4. Cross-source auth policy coverage (IAGE + Akamai unified):**
```cypher
MATCH (n)-[:USES_AUTHENTICATION_POLICY|USES_AUTHENTICATION_BEHAVIOR]->(ap:AuthenticationPolicy)
WHERE n:IntuitApiGatewayEnvironment OR n:AkamaiPropertyRule
RETURN ap.name, labels(n)[0] AS source_type, n.name AS config_name
ORDER BY ap.name
```

**5. Proxy-layer graph (all Proxy nodes and their paths):**
```cypher
MATCH (p:Proxy)
OPTIONAL MATCH (e:Endpoint)-[:SERVICED_BY]->(p)
OPTIONAL MATCH (p)-[:HAS_PATH|HAS_RULE]->(path_node)
OPTIONAL MATCH (path_node)-[:ROUTES_TO]->(backend:Endpoint)
RETURN p, e, path_node, backend
```

**6. Properties with SiteShield but no WAF (security gap query):**
```cypher
MATCH (p:AkamaiProperty)-[:ROUTES_THROUGH]->(ss:AkamaiSiteshieldMap)
WHERE NOT (p)-[:OFFLOADS_CONFIGURATION_TO]->(:AkamaiCloudlet)
AND NOT (:Endpoint)-[:SERVICED_BY]->(p)-[:HAS_RULE]->(:AkamaiPropertyRule)-[:USES_AUTHENTICATION_BEHAVIOR]->(:AuthenticationPolicy)
RETURN p.name, ss.rule_name
```

---

## Section 7: Open Questions

### Q1: Rule name stability and key collision

Rule names in Akamai properties are human-editable strings. If a rule is renamed, the old `AkamaiPropertyRule` node remains and the new one is created, leaving orphans until TTL cleanup. For a property with duplicate rule names (e.g., two rules both named "Default"), keys will collide and the second rule's data will overwrite the first.

**Recommendation:** After establishing the pattern, consider adding `rule_depth` to the key: `(property_id, rule_name, rule_depth)`. Depth is stable for the same rule unless the rule tree is reorganized. Alternatively, use the JSONPath position as a stable key component, but this is not human-readable and breaks on any tree reorder.

### Q2: Default rule extraction

The root rule (named `"default"` or the property name) contains behaviors that apply to ALL traffic. It should be extracted as a special `AkamaiPropertyRule` with `rule_name = "default"` and `pathCriteria = None`. This rule typically contains the default origin (the catch-all) and sometimes the primary security behaviors. This is the closest equivalent to a gateway environment's top-level `auth_protocols`.

### Q3: Multi-level criteria inheritance

The current `collate_origins_with_criteria` logic builds combined path criteria by taking the Cartesian product of criteria at each level. The new extractor should follow the same logic to avoid creating misleading path criteria. The challenge is that a rule at depth 3 may have criteria from three nested levels ANDed together, producing long combined strings. This is correct semantically but verbose.

**Recommendation:** Store both `path_criteria` (combined, ANDed) and also consider a `raw_path_criteria` property with just the criteria at this rule's level.

### Q4: Ownership attribution gap

Without a mapping between Akamai propertyIds and Intuit assetIds, `OWNED_BY` cannot be populated. Three approaches:
1. Use the Akamai property `name` to fuzzy-match against `Asset.normalized_asset_alias` (risky — naming conventions not enforced)
2. Use the `groupId` to group → contract → Intuit cost center → asset (requires an intermediate mapping table)
3. Leave `OWNED_BY` unimplemented and note it as a manual enrichment step

The reference implementation's `IMPLICITLY_OWNED_BY` for backend endpoints (inferring from mesh DNS) has no Akamai equivalent since origin hostnames are plain DNS, not mesh FQDNs.

### Q5: Conditional origin (cloudlet ALB) handling

Origins routed via the `cloudletsOrigin` behavior (ALB cloudlet) use a `conditional_origin_id` (a string ID like `"dc1_impot_ca_prod"`). The `collate_origins_with_criteria` function already captures these as `Origin(name=origin_host, conditional_origin=cdid)`. For the rule-level model, these should emit a `ROUTES_TO` relationship with `conditional_origin_id` set, pointing to the origin `Endpoint` node. The cloudlet that evaluates the origin is already linked via `OFFLOADS_CONFIGURATION_TO`.

### Q6: Staging property pipeline

The `staging-property.yaml` pipeline creates `AkamaiStagingProperty` nodes. Should staging rules also get the `AkamaiPropertyRule` treatment? Given that staging properties represent development/pre-production configurations, it may be valuable to model them separately:
- Either add a `staging: true` property on `AkamaiPropertyRule` nodes emitted from staging
- Or create a `AkamaiStagingPropertyRule` node type (adds complexity)
- Or skip staging rules entirely for the initial implementation

**Recommendation:** Skip for v1 and add a `network: production|staging` property in a follow-up.

### Q7: Fan-out mitigation for large shared properties

Some Akamai accounts have "shared" properties that serve dozens or hundreds of hostnames for different teams. A property with 80 frontend hostnames × 15 rule children × 3 origins per rule = 3,600 `ROUTES_TO` records per run. This is acceptable for Neo4j but merits monitoring.

### Q8: Integration with existing `PROXIES_TO` relationship

The existing `PROXIES_TO` relationship from `AkamaiProperty` to `Endpoint` (backend origin) is a coarse aggregate (all origins, de-duped, with path as a relationship property). With the new `HAS_RULE → ROUTES_TO` chain, `PROXIES_TO` becomes redundant at the fine-grained level. However, it should be **retained** because:
1. It enables simpler queries that don't need rule-level detail
2. It is already established in entity-queries.yaml (mongo queries reference it)
3. The two relationships serve different purposes (coarse vs. fine-grained routing)

### Q9: `ROUTES_TO` relationship type conflict

The `ROUTES_TO` relationship type already exists in the schema (from the services-registry model: `Path -[ROUTES_TO]-> Endpoint`). The new usage (`AkamaiPropertyRule -[ROUTES_TO]-> Endpoint`) reuses the same relationship type. This is intentional and desirable — it allows cross-source Cypher queries over the same relationship type — but means the new migration must NOT create `ROUTES_TO` (it already exists) and must only add new properties to it.

The existing `ROUTES_TO` properties are: `target_name`, `target_raw_dns`, `target_mesh_dns`, `target_workload_env_selector`. The new Akamai-specific properties (`path_criteria`, `hostname_criteria`, `origin_type`, `conditional_origin_id`) will be `null` on existing service-registry `ROUTES_TO` edges and `null` on new Akamai edges for the old properties. This is acceptable.

---

## Appendix A: Complete File List for the Implementation

### New files to create in nodestream-plugin-akamai:
- `nodestream_akamai/property_rule/__init__.py`
- `nodestream_akamai/property_rule/property_rule.py` — `AkamaiPropertyRuleExtractor`
- `nodestream_akamai/property-rule.yaml` — 4-pass pipeline YAML

### Modified files in nodestream-plugin-akamai:
- `nodestream_akamai/akamai_utils/model.py` — add `PropertyRuleRecord` dataclass
- `nodestream_akamai/akamai_utils/property_client.py` — add `extract_rule_records()`, `extract_security_behaviors()`
- `nodestream_akamai/property.yaml` — add `additional_types: [Proxy]` to source_node
- `nodestream_akamai/staging-property.yaml` — optionally add Proxy label

### New files to create in endpoint-graph-ingest:
- `migrations/20260615140000.yaml` — creates `AkamaiPropertyRule`, `HAS_RULE`, `USES_AUTHENTICATION_BEHAVIOR`, extends `ROUTES_TO`

---

## Appendix B: Existing Schema Reference (Akamai Nodes in endpoint-graph-ingest)

From migration 20240403150846 and subsequent migrations:

| Node Type | Key | Core Properties |
|---|---|---|
| `AkamaiProperty` | `id` | `name`, `version`, `rule_format`, `deeplink` |
| `AkamaiStagingProperty` | `id` | same |
| `AkamaiWafConfig` | `config_id` | `config_name`, `production_version`, `deeplink` |
| `AkamaiWafPolicy` | `policy_id` | `policy_name`, `deeplink` |
| `AkamaiCloudlet` | `id` | `name`, `type`, `active_production_version`, etc. |
| `AkamaiGtmDomain` | `name` | `type`, `loadImbalancePercentage`, etc. |
| `AkamaiGtmProperty` | `fqdn` | `name`, `type` |
| `AkamaiEdgeHostname` | `edge_hostname_id` | `edge_hostname`, `ip_version_behavior` |
| `AkamaiEdnsZone` | `zone` | `type`, `contract_id`, `alias_count` |
| `AkamaiEdnsRecordSet` | `key` | `name`, `type`, `ttl` |
| `AkamaiDiscoveredAPI` | `id` | `host`, `basePath`, traffic metrics |
| `AkamaiRedirectConfig` | `policyId` | `name`, `deeplink` |
| `AkamaiSiteshieldMap` | `rule_name` | `id`, `map_alias`, `sure_route_name` |
| `AkamaiIvmPolicySet` | `id` | — |
| `AkamaiCPCode` | `id` | `cpcode_name`, `contract_id`, `group_id` |
| `AkamaiCertificate` | `id` | `expiry`, `cn`, `cipher_suite` |

| Relationship | Notes |
|---|---|
| `SERVICED_BY` | Endpoint → AkamaiProperty (front-door FQDNs) |
| `PROXIES_TO` | AkamaiProperty → Endpoint (backend origins) |
| `PROTECTED_BY` | Endpoint → AkamaiWafPolicy |
| `INCLUDED_IN` | AkamaiWafPolicy → AkamaiWafConfig |
| `OFFLOADS_CONFIGURATION_TO` | AkamaiProperty → AkamaiCloudlet |
| `MEDIA_OPTIMIZED_BY` | AkamaiProperty → AkamaiIvmPolicySet |
| `RUNS_CODE_FOR` | AkamaiEdgeworker → AkamaiProperty |
| `ROUTES_THROUGH` | AkamaiProperty → AkamaiSiteshieldMap |
| `REDIRECTS_IN` | AkamaiProperty → AkamaiRedirectConfig |
| `REPORTS_ON` | AkamaiCPCode → AkamaiProperty |
| `CNAMES_TO` | Endpoint → AkamaiEdgeHostname |
| `EGRESS` | AkamaiSiteshieldMap → Cidripv4 |
| `IN_DOMAIN` | AkamaiGtmProperty → AkamaiGtmDomain |
| `RESOLVES_TO` | AkamaiGtmProperty/AkamaiEdnsRecordSet → Endpoint/Cidripv4/Cidripv6 |
| `RECORD_OF` | AkamaiEdnsRecordSet → AkamaiEdnsZone |
| `ENCRYPTED_BY` | Endpoint → AkamaiCertificate |
| `REDIRECTS_HANDLED_BY` | Endpoint → AkamaiRedirectConfig |
| `REDIRECTS_TO` | AkamaiRedirectConfig → Endpoint |
