from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from logging import getLogger
from threading import current_thread
from typing import Any, Dict, List, Tuple

LOGGER = getLogger(__name__)

JsonDocument = Dict[str, Any]


def default_metadata():
    """Generates default metadata containing of time and pipeline name."""
    return Metadata(dict(last_ingested_at=datetime.utcnow(), pipeline_name=current_thread().name))


def default_var():
    """Generates default variables"""
    return GlobalVariable(dict())


def default_related_metadata():
    return Metadata(dict(last_linked_at=datetime.utcnow()))


class IngestionHook(ABC):
    """An IngestionHook is a custom piece of logic that is bundled as a query.

    IngestionHooks provide a mechanism to enrich the graph model that is derived from
    data added to and currently existing in the graph. For example, drawing an edge
    between two nodes where following a complex path.
    """

    @abstractmethod
    def as_cypher_query_and_parameters(self) -> Tuple[str, Dict[str, Any]]:
        """Returns a cypher query string and parameters to execute."""

        raise NotImplementedError


class Metadata(dict):
    """Used by `SourceNode` and `Relationship`. Provides a store for `metadata`."""

    def add_metadata(self, key: str, value: Any):
        """Put a new key,value pair into the metadata of the object.

        Overrides the value if already present.
        """
        self[key] = value


class GlobalVariable(dict):
    """Used by `SourceNode` and `Relationship`. Provides a store for `global_var`."""

    def add_global_var(self, key: str, value: Any):
        """Put a new key,value pair into the global_var of the object.

        Overrides the value if already present.
        """
        self[key] = value


@dataclass
class SourceNode:
    """A `SourceNode` is the center of ingestion.

    Its the node that relationships are drawn to or from depending on the
    direction of the relationship.
    """

    type: str
    identity_values: Dict[str, Any]
    metadata: Metadata = field(default_factory=default_metadata)


@dataclass
class Relationship:
    """Stores information about the related node and the relationship itself."""

    related_node_type: str
    relationship_type: str
    related_node_identity_field_value: str
    related_node_identity_field_name: str = "id"
    metadata: Metadata = field(default_factory=default_metadata)
    related_metadata: Metadata = field(default_factory=default_related_metadata)

    def relation_identity(self) -> Dict[str, Any]:
        """The identity (primary key values) for the node that the relationship is connecting to.

        Returns:
            The identity of the relationship as key,value pairs.
        """
        return {self.related_node_identity_field_name: str(self.related_node_identity_field_value).lower()}


class IngestionStrategy(ABC):
    """ """

    @abstractmethod
    def ingest_source_node(self, source: SourceNode):
        """_summary_

        Args:
            source (SourceNode): _description_
        """
        raise NotImplementedError

    @abstractmethod
    def ingest_inbound_relationship(self, source: SourceNode, inbound: Relationship):
        """_summary_

        Args:
            source (SourceNode): _description_
            inbound (Relationship): _description_
        """
        raise NotImplementedError

    @abstractmethod
    def ingest_outbound_relationship(self, source: SourceNode, outbound: Relationship):
        """_summary_

        Args:
            source (SourceNode): _description_
            outbound (Relationship): _description_
        """
        raise NotImplementedError

    @abstractmethod
    def run_hook(self, hook: IngestionHook):
        """_summary_

        Args:
            hook (IngestionHook): The `IngestionHook` that should be run.
        """
        raise NotImplementedError

    @abstractmethod
    def upsert_key_index(self, index: "KeyIndex"):
        raise NotImplementedError

    @abstractmethod
    def upsert_field_index(self, index: "FieldIndex"):
        raise NotImplementedError


@dataclass(frozen=True)
class KeyIndex:
    type: str
    identity_keys: frozenset

    def ingest(self, strategy: IngestionStrategy):
        strategy.upsert_key_index(self)


@dataclass(frozen=True)
class FieldIndex:
    type: str
    field: str

    def ingest(self, strategy: IngestionStrategy):
        strategy.upsert_field_index(self)


@dataclass
class DesiredIngestion:
    source: SourceNode = None
    global_var: GlobalVariable = field(default_factory=default_var)
    inbound_connections: List[Relationship] = field(default_factory=list)
    outbound_connections: List[Relationship] = field(default_factory=list)
    before_ingest_hooks: List[IngestionHook] = field(default_factory=list)
    after_ingest_hooks: List[IngestionHook] = field(default_factory=list)

    @property
    def identity_is_valid(self) -> bool:
        """An identity is only invalid if _all_ of the key,value pairs for it is None."""
        return not all(value is None for value in self.source.identity_values.values())

    def ingest_source_node(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        strategy.ingest_source_node(self.source)

    def ingest_inbound_relationships(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        for inbound_connection in self.inbound_connections:
            strategy.ingest_inbound_relationship(self.source, inbound_connection)

    def ingest_outbound_relationships(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        for outbound_connection in self.outbound_connections:
            strategy.ingest_outbound_relationship(self.source, outbound_connection)

    def run_after_ingest_hooks(self, strategy: IngestionStrategy):
        for hook in self.after_ingest_hooks:
            strategy.run_hook(hook)

    def run_before_ingest_hooks(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        for hook in self.before_ingest_hooks:
            strategy.run_hook(hook)

    def ingest(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        if not self.identity_is_valid:
            LOGGER.warning(
                "Identity value for source node was null. Skipping Ingest.",
                extra=asdict(self),
            )
            return

        self.run_before_ingest_hooks(strategy)
        self.ingest_source_node(strategy)
        self.ingest_inbound_relationships(strategy)
        self.ingest_outbound_relationships(strategy)
        self.run_after_ingest_hooks(strategy)

    def create_inbound_relationship(self, relationship: Relationship):
        """_summary_

        Args:
            relationship (Relationship): _description_
        """
        self.inbound_connections.append(relationship)

    def create_outbound_relationship(self, relationship: Relationship):
        """_summary_

        Args:
            relationship (Relationship): _description_
        """
        self.outbound_connections.append(relationship)

    def add_ingest_hook(self, ingest_hook: IngestionHook, run_before_ingest=False):
        """_summary_

        Args:
            ingest_hook (IngestionHook): _description_
        """
        if run_before_ingest:
            self.before_ingest_hooks.append(ingest_hook)
        else:
            self.after_ingest_hooks.append(ingest_hook)


@dataclass
class MultiNodeIngestion:
    items: List[DesiredIngestion]

    def ingest(self, strategy: IngestionStrategy):
        """_summary_

        Args:
            strategy (IngestionStrategy): _description_
        """
        for item in self.items:
            item.ingest(strategy)
