from copy import deepcopy
from logging import getLogger
from typing import Iterable, Optional

from jmespath.parser import ParsedResult

from ..interpretations import Paradigm
from ..model import DesiredIngestion, MultiNodeIngestion
from .abc import InterpreterAbc

LOGGER = getLogger(__name__)


class Interpreter(InterpreterAbc):
    def __init__(
        self,
        interpretations: Iterable[dict],
        iterate_on: Optional[ParsedResult] = None,
        global_enrichment: Optional[Iterable[dict]] = None,
    ) -> None:
        super().__init__()
        if global_enrichment and not iterate_on:
            raise ValueError(
                "global_enrichment is applied when not iterating on sub-objects"
            )

        self.iterate_on = iterate_on
        self.interpretations = Paradigm.from_raw_arguments(interpretations)
        self.global_enrichment = Paradigm.from_raw_arguments(global_enrichment or [])

    def get_base_ingestion(self, item):
        self.global_enrichment.apply_to_ingestion(item, ingestion := DesiredIngestion())
        return ingestion

    def interpret(self, item):
        LOGGER.debug("Received this event from extractor: %s", item)
        base_ingestion = self.get_base_ingestion(item)

        def interpret(item):
            ingestion = deepcopy(base_ingestion)
            self.interpretations.apply_to_ingestion(item, ingestion)
            return ingestion

        if self.iterate_on:
            items_to_iterate_over = self.iterate_on.search(item) or []
            ingested_items = [interpret(sub_item) for sub_item in items_to_iterate_over]
            return MultiNodeIngestion(ingested_items)

        return interpret(item)

    def gather_used_indices(self):
        return self.interpretations.gather_used_indices().union(
            self.global_enrichment.gather_used_indices()
        )
