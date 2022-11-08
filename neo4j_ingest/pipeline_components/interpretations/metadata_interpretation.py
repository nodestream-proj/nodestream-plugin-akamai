from ..model import DesiredIngestion, JsonDocument
from .interpretation import Interpretation


class MetadataInterpretation(Interpretation, type="metadata"):
    """Adds additional metadata to the source node. These are added as fields on the node in the graph database.

    To use this, in a pipeline file, in the `interpretations` section, add a block like this.

    ```
    interpretations:
      # ...
      - type: metadata
        name: !!python/jmespath data.foo.name
        home_town: !!python/jmespath data.foo.homeTown
    ```

    This will result in adding a `name` and/or `home_town` to the source node metadata
    so long as that jmespath search returns a value.
    """

    def __init__(self, **searches) -> None:
        self.searches = searches

    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        self.apply_searches_as_metadata(
            data, desired_ingest.source.metadata, desired_ingest, **self.searches
        )
