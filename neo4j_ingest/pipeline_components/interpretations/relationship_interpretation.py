from typing import Any, Dict, Optional

from ..model import DesiredIngestion, JsonDocument, KeyIndex, Relationship
from .interpretation import Interpretation


class RelationshipInterpretation(Interpretation, type="relationship"):
    """Provides a generic method by which to interpret a relationship between the source node and zero-to-many related nodes.

    To use this, in a pipeline file, in the `interpretations` section, add a block like this.

    ```yaml
    interpretations:
      # ...
      - type: relationship
        related_node_type: TheOtherTypeYouAreLinkingTo
        relationship_type: IS_QUANTUMLY_ENTANGLED_WITH
        search: !!python/jmespath the.path.to.what.to.join.on
        related_field_name: field_name_to_join_on # optional, defaults to ID.
        outbound: false  # optional, defaults to true
        find_many: true  # optional. default to false
    ```
    """

    def __init__(
        self,
        related_node_type: str,
        relationship_type: str,
        search: str,
        related_field_name: str = "id",
        outbound: bool = True,
        find_many: bool = False,
        iterate_on: list = None,
        related_metadata: Optional[Dict[str, Any]] = None,
        **metadata_searches,
    ):
        self.related_node_type = related_node_type
        self.related_field_name = related_field_name
        self.relationship_type = relationship_type
        self.search = search
        self.outbound = outbound
        self.find_many = find_many
        self.iterate_on = iterate_on
        self.metadata_searches = metadata_searches
        self.related_metadata = related_metadata or {}

    def find_matches(self, data: JsonDocument, desired_ingest):
        if self.find_many:
            return self.search_many_search_patterns_for_values_without_trailing_dots(
                data, self.search
            )
        else:
            if (
                item := self.search_for_single_value(data, self.search, desired_ingest)
            ) is not None:
                return [item]
            else:
                return []

    def make_relationship(self, matched_value: str, data: JsonDocument, desired_ingest):
        relationship = Relationship(
            related_node_type=self.related_node_type,
            relationship_type=self.relationship_type,
            related_node_identity_field_value=matched_value,
            related_node_identity_field_name=self.related_field_name,
        )
        self.apply_searches_as_metadata(
            data, relationship.metadata, desired_ingest, **self.metadata_searches
        )
        self.apply_searches_as_metadata(
            data, relationship.related_metadata, desired_ingest, **self.related_metadata
        )
        return relationship

    def find_relationships(self, data: JsonDocument, desired_ingest):
        return [
            self.make_relationship(match, data, desired_ingest)
            for match in self.find_matches(data, desired_ingest)
        ]

    def store_relationship(
        self, relationship: Relationship, desired_ingest: DesiredIngestion
    ):
        if self.outbound:
            desired_ingest.create_outbound_relationship(relationship)
        else:
            desired_ingest.create_inbound_relationship(relationship)

    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        # Parse the input data if provided a list to iterate on.
        docs_to_search = (
            [data]
            if self.iterate_on is None
            else self.search_for_many_values(data, self.iterate_on)
        )
        for doc in docs_to_search:
            for relationship in self.find_relationships(doc, desired_ingest):
                self.store_relationship(relationship, desired_ingest)

    def gather_used_indices(self):
        yield KeyIndex(self.related_node_type, frozenset({self.related_field_name}))
