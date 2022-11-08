from dataclasses import dataclass

from ..model import IngestionHook

ATTRIBUTION_QUERY = """
MATCH (endpoint:Endpoint{fqdn: $fqdn})
OPTIONAL MATCH (endpoint)<-[:RESOLVES_TO]-()<-[:DEFINED_BY]-(second_degree:Endpoint)
OPTIONAL MATCH (second_degree)<-[:RESOLVES_TO]-()<-[:DEFINED_BY]-(third_degree:Endpoint)
WITH endpoint, coalesce(third_degree, second_degree, endpoint) as target LIMIT 1
CALL apoc.path.spanningTree(target, {
    relationshipFilter: "CONTAINED_IN>|DEFINED_BY>|EXPERIENCE_PROVIDED_BY>|OWNED_BY>|PROXIES_TO|RESOLVES_TO>|<ASSOCIATED_TO|SERVICED_BY>|COMPOSED_WITH>",
    labelFilter: ">Asset",
    minLevel: 1,
    maxLevel: 10,
    limit: 5
})
YIELD path as path
WITH endpoint, last(nodes(path)) as asset, {
    hops: length(path),
    starting_fqdn: target.fqdn,
    last_ingested_at: datetime()
} as props
MERGE (endpoint)-[r:ATTRIBUTED_TO]->(asset)
ON CREATE SET r+= props
ON MATCH SET r+= props
"""


@dataclass
class AttributeEndpoint(IngestionHook):
    """An IngestionHook where the defined endpoint is attributed to assets.

    It executes a complex query and draws an `ATTRIBUTED_TO` edge between the endpoint and the asset.
    """

    fqdn: str

    def as_cypher_query_and_parameters(self):
        return ATTRIBUTION_QUERY, {"fqdn": self.fqdn}
