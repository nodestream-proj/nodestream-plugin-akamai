from typing import List

from neo4j import Transaction

from ..model import (
    DesiredIngestion,
    FieldIndex,
    IngestionHook,
    IngestionStrategy,
    KeyIndex,
    Relationship,
    SourceNode,
)

# $metadata is set twice so that we set the values on both create and match (allows for updates)
NODE_INGEST_QUERY = "CALL apoc.merge.node($node_types, $identity, $metadata, $metadata) YIELD node RETURN true"
INBOUND_RELATION_QUERY = """
CALL apoc.merge.node($target_node_types, $target_identity) yield node as source
CALL apoc.merge.node(
    $related_node_types,
    $related_identity,
    $related_metadata,
    $related_metadata
)
yield node as related
CALL apoc.merge.relationship(
    related,
    $relationship_type,
    {},
    $metadata,
    source,
    $metadata
) yield rel as rel
RETURN true;
"""
OUTBOUND_RELATION_QUERY = """
CALL apoc.merge.node($target_node_types, $target_identity) yield node as source
CALL apoc.merge.node(
    $related_node_types,
    $related_identity,
    $related_metadata,
    $related_metadata
)
yield node as related
CALL apoc.merge.relationship(
    source,
    $relationship_type,
    {},
    $metadata,
    related,
    $metadata
) yield rel as rel
RETURN true;
"""

COMMIT_QUERY = """
UNWIND $queries as query
CALL apoc.cypher.doIt(query.statement, query.parameters) YIELD value
RETURN true
"""

KEY_INDEX_QUERY_FORMAT = "CREATE CONSTRAINT {constraint_name} IF NOT EXISTS FOR (n:{type}) REQUIRE ({key_pattern}) IS NODE KEY"
FIELD_INDEX_QUERY_FORMAT = (
    "CREATE INDEX {constraint_name} IF NOT EXISTS FOR (n:{type}) ON (n.{field})"
)


def key_index_as_query(key: KeyIndex):
    key_pattern = ",".join(f"n.{prop}" for prop in sorted(list(key.identity_keys)))
    constraint_name = f"{key.type}_node_key"
    return KEY_INDEX_QUERY_FORMAT.format(
        constraint_name=constraint_name, key_pattern=key_pattern, type=key.type
    )


def field_index_as_query(index: FieldIndex):
    constraint_name = f"{index.type}_{index.field}_additional_index"
    return FIELD_INDEX_QUERY_FORMAT.format(
        constraint_name=constraint_name, type=index.type, field=index.field
    )


class Neo4jIngestionStrategy(IngestionStrategy):
    def __init__(self, transaction: Transaction) -> None:
        self.transaction = transaction
        self.queries = []

    def execute(self, query, **kwargs):
        self.queries.append({"statement": query, "parameters": kwargs})

    def execute_related_query(
        self, source: SourceNode, relation: Relationship, query: str
    ):
        self.execute(
            query,
            target_identity=source.identity_values,
            target_node_types=[source.type],
            related_identity=relation.relation_identity(),
            related_node_types=[relation.related_node_type],
            relationship_type=relation.relationship_type,
            related_metadata=relation.related_metadata,
            metadata=relation.metadata,
        )

    def ingest_source_node(self, source: SourceNode):
        self.execute(
            NODE_INGEST_QUERY,
            identity=source.identity_values,
            node_types=[source.type],
            metadata=source.metadata,
        )

    def ingest_inbound_relationship(self, source: SourceNode, relation: Relationship):
        self.execute_related_query(source, relation, INBOUND_RELATION_QUERY)

    def ingest_outbound_relationship(self, source: SourceNode, relation: Relationship):
        self.execute_related_query(source, relation, OUTBOUND_RELATION_QUERY)

    def run_hook(self, hook: IngestionHook):
        query, params = hook.as_cypher_query_and_parameters()
        self.execute(query, **params)

    def upsert_key_index(self, index: KeyIndex):
        self.execute(key_index_as_query(index))

    def upsert_field_index(self, index: FieldIndex):
        self.execute(field_index_as_query(index))

    def finish(self):
        self.transaction.run(COMMIT_QUERY, queries=self.queries)

    @classmethod
    def ingest(cls, transaction: Transaction, items: List[DesiredIngestion]):
        # Ingest a single batch in a transaction as opposed to a single
        # item so that we reduce the amount of overhead caused by transactions.
        strategy = cls(transaction)
        for item in items:
            item.ingest(strategy)
        strategy.finish()
