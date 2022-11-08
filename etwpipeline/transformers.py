import logging
from abc import abstractmethod
from typing import Any, Callable, Generator, List

from dateutil import parser

from .step import Step


class Transformer(Step):
    def handle_item(self, item):
        val_or_gen = self.transform(item)
        if isinstance(val_or_gen, Generator):
            yield from val_or_gen
        else:
            yield val_or_gen

    @abstractmethod
    def transform(self, item):
        raise NotImplementedError

    @classmethod
    def from_callable(cls, pure_function: Callable[[Any], Any]):
        return CallableTransformer(pure_function)


class CallableTransformer(Transformer):
    def __init__(self, pure_function: Callable[[Any], Any]) -> None:
        self.pure_function = pure_function

    def transform(self, item):
        return self.pure_function(item)


class DatetimeParser(Transformer):
    def __init__(self, key_list: List[str]) -> None:
        self.key_list = key_list
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_datetime(self, item, key):
        value = None
        try:
            value = item[key]
            if value is not None:
                item[key] = parser.parse(value)
        except Exception:
            self.logger.exception("Error parsing datetime: %s=%s", key, value)

    def transform(self, item):
        for key in self.key_list:
            self.parse_datetime(item, key)
        return item
