import os
from abc import abstractmethod

from etwpipeline import Transformer


class InterpreterAbc(Transformer):
    def __init__(self) -> None:
        self._has_pushed_indices = False
        self._should_push_indices = (
            os.environ.get("AUTO_GENERATE_INDICES", "false") == "true"
        )

    @abstractmethod
    def gather_used_indices(self):
        raise NotImplementedError

    @abstractmethod
    def interpret(self, item):
        raise NotImplementedError

    def transform(self, item):
        if not self._has_pushed_indices and self._should_push_indices:
            yield from self.gather_used_indices()
            self._has_pushed_indices = True

        yield self.interpret(item)
