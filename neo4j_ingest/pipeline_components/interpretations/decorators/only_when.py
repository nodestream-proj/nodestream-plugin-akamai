from ...model import DesiredIngestion
from ..interpretation import Interpretation, JsonDocument


class OnlyWhenInterpretationDecorator(Interpretation, type="only_when", decorator=True):
    def __init__(self, wrapped_interpretation: Interpretation, search, equals) -> None:
        self.wrapped_interpretation = wrapped_interpretation
        self.search = search
        self.equals = equals

    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        if (
            self.search_for_single_value(data, self.search, desired_ingest)
            == self.equals
        ):
            self.wrapped_interpretation.interpret(data, desired_ingest)
