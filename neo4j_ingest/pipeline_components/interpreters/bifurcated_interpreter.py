from .abc import InterpreterAbc
from .interpreter import Interpreter


class BifurcatedInterpreter(InterpreterAbc):
    def __init__(self, split_on, paradigms) -> None:
        super().__init__()
        self.split_on = split_on
        self.paradigms = {
            paradigm["match_value"]: Interpreter(**paradigm["arguments"])
            for paradigm in paradigms
        }

    def interpret(self, item):
        value_to_look_for = item[self.split_on]
        if value_to_look_for not in self.paradigms:
            raise ValueError(f"'{value_to_look_for}' was not matched in splitting")
        return self.paradigms[value_to_look_for].interpret(item)

    def gather_used_indices(self):
        return {
            index
            for paradigm in self.paradigms.values()
            for index in paradigm.gather_used_indices()
        }
