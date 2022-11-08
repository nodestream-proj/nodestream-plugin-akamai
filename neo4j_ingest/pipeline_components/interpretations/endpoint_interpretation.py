from ..ingestion_hooks.endpoint_attribution import AttributeEndpoint
from ..model import DesiredIngestion, Relationship
from .relationship_interpretation import RelationshipInterpretation


class EndpointInterpretation(RelationshipInterpretation, type="endpoint"):
    """Builds relationships for endpoints.

    ```yaml
    interpretations:
      # ...
      - type: endpoint
        relationship_type: IS_QUANTUMLY_ENTANGLED_WITH
        search: !!python/jmespath the.path.to.what.to.join.on
        outbound: false # defaults to true
    ```
    you may also search multiple locations like so:

    ```yaml
    interpretations:
      # ...
      - type: endpoint
        relationship_type: IS_QUANTUMLY_ENTANGLED_WITH
        search:
            - !!python/jmespath the.path.to.what.to.join.on
            - !!python/jmespath the.other.path.to.join.on
    ```
    """

    def __init__(
        self,
        relationship_type: str,
        search: str,
        outbound: bool = True,
    ):
        super().__init__(
            related_node_type="Endpoint",
            relationship_type=relationship_type,
            search=search,
            related_field_name="fqdn",
            outbound=outbound,
            find_many=True,
        )

    def store_relationship(
        self, relationship: Relationship, desired_ingest: DesiredIngestion
    ):
        super().store_relationship(relationship, desired_ingest)
        desired_ingest.add_ingest_hook(
            AttributeEndpoint(fqdn=relationship.related_node_identity_field_value)
        )
