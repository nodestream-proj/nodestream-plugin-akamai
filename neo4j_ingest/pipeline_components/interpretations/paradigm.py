from typing import Iterable

from ..model import DesiredIngestion, JsonDocument
from .interpretation import Interpretation


class Paradigm:
    @classmethod
    def from_raw_arguments(cls, interpretations):
        interpretations = [Interpretation.from_type(**data) for data in interpretations]
        return cls(interpretations)

    def __init__(self, interpretations: Iterable[Interpretation]) -> None:
        self.interpretations = interpretations

    def apply_to_ingestion(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        for interpretation in self.interpretations:
            interpretation.interpret(data, desired_ingest)

    def gather_used_indices(self):
        return {
            index
            for interpretation in self.interpretations
            for index in interpretation.gather_used_indices()
        }
