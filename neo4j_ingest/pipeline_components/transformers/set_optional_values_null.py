from etwpipeline import Transformer


class SetOptionalValuesNull(Transformer):
    def __init__(self, keys):
        self.keys = keys

    def transform(self, item):
        item.update({key: item.get(key) for key in self.keys})
        return item
