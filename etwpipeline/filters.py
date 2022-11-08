from abc import abstractmethod

from .step import Step


class Filter(Step):
    def handle_item(self, item):
        if not self.should_filter(item):
            yield item

    @abstractmethod
    def should_filter(self, item):
        raise NotImplementedError


class DictionaryKeyFilter(Filter):
    def __init__(self, matches, allow_non_dictionaries=False):
        self.allow_non_dictionaries = allow_non_dictionaries
        self.matches = matches

    def should_filter(self, item):
        if not isinstance(item, dict):
            return not self.allow_non_dictionaries

        for key, expected_value in self.matches.items():
            if key not in item:
                return True

            actual_value = item[key]
            if isinstance(expected_value, dict):
                recursive_filter = DictionaryKeyFilter(
                    expected_value, allow_non_dictionaries=self.allow_non_dictionaries
                )
                if recursive_filter.should_filter(actual_value):
                    return True
            else:
                if actual_value != expected_value:
                    return True

        return False


class FirstNFilter(Filter):
    def __init__(self, count: int = 1):
        self.remaining = int(count)

    def should_filter(self, item):
        if self.remaining > 0:
            self.remaining -= 1
            return False
        return True
