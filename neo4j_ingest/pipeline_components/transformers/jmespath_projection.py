from etwpipeline import Transformer
from jmespath.parser import ParsedResult


class JmespathProjection(Transformer):
    def __init__(self, projection: ParsedResult) -> None:
        self.projection = projection

    def transform(self, item):
        yield from self.projection.search(item)
