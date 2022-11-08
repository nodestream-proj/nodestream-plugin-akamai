from abc import ABC, abstractmethod
from typing import Any, Generator

from .extractors import Extractor

_join_method_strategy = {}


class JoinStrategy(ABC):
    @abstractmethod
    def join_with_data(self, left_unmatched, paired, right_unmatched):
        raise NotImplementedError

    def __init_subclass__(cls, method_name=None) -> None:
        _join_method_strategy[method_name] = cls

    @classmethod
    def by_name(cls, name, *args, **kwargs):
        return _join_method_strategy[name](*args, **kwargs)


class InnerJoinStrategy(JoinStrategy, method_name="inner"):
    def join_with_data(self, _, paired, __):
        yield from paired


class FullOuterJoin(JoinStrategy, method_name="full"):
    def join_with_data(self, left_unmatched, paired, right_unmatched):
        yield from left_unmatched
        yield from paired
        yield from right_unmatched


class LeftOuterJoin(JoinStrategy, method_name="left"):
    def join_with_data(self, left_unmatched, paired, _):
        yield from left_unmatched
        yield from paired


class RightOuterJoin(JoinStrategy, method_name="right"):
    def join_with_data(self, _, paired, right_unmatched):
        yield from paired
        yield from right_unmatched


class Join(Extractor):
    def __init__(
        self,
        left_side: Generator[Any, None, None],
        right_side: Generator[Any, None, None],
        join_strategy: JoinStrategy,
        on: str,
    ) -> None:
        self.left_side = left_side
        self.right_side = right_side
        self.join_strategy = join_strategy
        self.on = on

    def match_items(self):
        # Now that we have the data of the two pipelines, we can join them into
        # three groups. One for left data that was unpaired, items that we can pair together,
        # and right data that was unpaired. Each join strategy uses those lists to determine what
        # goes forward.
        left_data_by_join_field = {item[self.on]: item for item in self.left_side}
        right_data_by_join_field = {item[self.on]: item for item in self.right_side}
        all_left_keys = left_data_by_join_field.keys()
        all_right_keys = right_data_by_join_field.keys()

        # We can use set difference on the left and right to get the keys only on one
        # side. We can also use intersection to find keys common to both sides.
        left_only_keys = all_left_keys - all_right_keys
        intersecting_keys = all_left_keys & all_right_keys
        right_only_keys = all_right_keys - all_left_keys

        def join_row(key):
            left_side_data = left_data_by_join_field.get(key, {})
            right_side_data = right_data_by_join_field.get(key, {})
            return {**left_side_data, **right_side_data}

        left_unmatched = [join_row(key) for key in left_only_keys]
        paired = [join_row(key) for key in intersecting_keys]
        right_unmatched = [join_row(key) for key in right_only_keys]

        return left_unmatched, paired, right_unmatched

    def extract_records(self):
        yield from self.join_strategy.join_with_data(*self.match_items())
