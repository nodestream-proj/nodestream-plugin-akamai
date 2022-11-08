from threading import current_thread
from typing import List, Optional

from ..model import (
    DesiredIngestion,
    FieldIndex,
    JsonDocument,
    KeyIndex,
    Relationship,
    SourceNode,
)
from .interpretation import Interpretation


class SourceNodeInterpretation(Interpretation, type="source_node"):
    """Central to all ingestions. Finds the core identity information for the node central to this ingest.

    To use this, in a pipeline file, in the `interpretations` section, add a block like this.

    ```yaml
    interpretations:
      # Conventionally, this should be first.
      - type: source_node
        node_type: TheTypeOfTheNodeYouAreIngesting
        identity_field_value: !!python/jmespath value_for_id_field
        identity_field_name: id
    ```
    """

    def __init__(
        self,
        node_type,
        additionally_index: Optional[List[str]] = None,
        **identity_values,
    ):
        self.node_type = node_type
        self.identity_values = identity_values
        self.additional_indexes = additionally_index or []

    def find_source_type(self, data: JsonDocument, desired_ingest):
        is_statically_defined = isinstance(self.node_type, str)
        return (
            self.node_type
            if is_statically_defined
            else self.search_for_single_value(data, self.node_type, desired_ingest)
        )

    def find_identity_values(self, data, desired_ingest):
        return {
            key: v.lower()
            if isinstance(
                v := self.search_for_single_value(data, value, desired_ingest), str
            )
            else v
            for key, value in self.identity_values.items()
        }

    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        desired_ingest.source = SourceNode(
            type=self.find_source_type(data, desired_ingest),
            identity_values=self.find_identity_values(data, desired_ingest),
        )
        # Add the creation of a relationship here to the current pipeline
        pipeline_rel = Relationship(
            related_node_type="Pipeline",
            relationship_type="DISCOVERED_BY",
            related_node_identity_field_value=current_thread().name,
            related_node_identity_field_name="pipeline_name",
        )
        desired_ingest.create_inbound_relationship(pipeline_rel)

    def gather_used_indices(self):
        yield KeyIndex(self.node_type, frozenset(self.identity_values.keys()))
        for field in self.additional_indexes:
            yield FieldIndex(self.node_type, field)
