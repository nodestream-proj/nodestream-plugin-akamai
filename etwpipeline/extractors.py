from abc import ABC, abstractmethod
from typing import Any, Generator


class Extractor(ABC):
    @abstractmethod
    def extract_records(self) -> Generator[Any, None, None]:
        raise NotImplementedError

    def join_to(self, right_side: "Extractor", on: str, method: str = "inner"):
        from .join import Join, JoinStrategy

        join_strategy = JoinStrategy.by_name(method)
        return Join(
            self.extract_records(), right_side.extract_records(), join_strategy, on
        )


class IterableExtractor(Extractor):
    def __init__(self, iterable) -> None:
        self.iterable = iterable

    def extract_records(self):
        yield from self.iterable


class EmptyExtractor(IterableExtractor):
    def __init__(self) -> None:
        super().__init__([])


class Flush:
    pass
