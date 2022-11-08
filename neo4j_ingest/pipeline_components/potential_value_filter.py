from typing import Iterable

from etwpipeline.filters import Filter


class PotentialValueFilter(Filter):
    def __init__(self, **value_matchers: Iterable[str]):
        self.value_matchers = value_matchers

    def should_filter(self, item):
        return not all(
            item.get(key) in allowed_values
            for key, allowed_values in self.value_matchers.items()
        )
