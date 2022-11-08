from ..model import DesiredIngestion, JsonDocument
from .interpretation import Interpretation


class GlobalVariableInterpretation(Interpretation, type="global_variable"):
    """Adds additional metadata to the source node. These are added as fields on the node in the graph database.

    To use this, in a pipeline file, in the `interpretations` section, add a block like this.

    ```
    interpretations:
      # ...
      - type: global_variable
        variable: your_variable_name
        value: !!python/jmespath data.foo.your_value
    ```

    This will result in adding a `your_variable_name` of `your_value` to the list of variables accessible
    to your global enrichments so long as that jmespath search returns a value.
    """

    def __init__(self, **searches) -> None:
        self.searches = searches

    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        self.apply_searches_as_global_var(
            data, desired_ingest.global_var, desired_ingest, **self.searches
        )
