import json
from typing import Iterable

from etwpipeline import Transformer


class ExpandJsonFields(Transformer):
    def __init__(self, field_names: Iterable[str]):
        self.field_names = field_names

    def transform(self, item):
        for field_name in self.field_names:
            item[field_name] = json.loads(item[field_name])
        return item
