from abc import ABC, abstractmethod

from .extractors import Flush


class Step(ABC):
    def perform_step_over_generator(self, generator):
        for item in generator:
            if item is Flush:
                yield item
            else:
                yield from self.handle_item(item)

    @abstractmethod
    def handle_item(self, item):
        pass
