from abc import ABC, abstractmethod
from functools import wraps

from jmespath.parser import ParsedResult

from neo4j_ingest.orchestration import GlobalVariableLoader

from ..model import DesiredIngestion, JsonDocument

_interpretation_types = {}
_interpretation_decorator_types = {}


def deduplicate_returned_list(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # You might by wondering, why? Well let me tell you. This turned out
        # to be the most simplistic way to both have an ordered collection and
        # deduplicate values seen more than once. The ordering is required so
        # we can have a stable set of tests.
        result = f(*args, **kwargs)
        seen = set()
        return [x for x in result if x not in seen and not seen.add(x)]

    return decorator


def _decompose_args(kwargs):
    decorators = {
        key: value
        for key, value in kwargs.items()
        if key in _interpretation_decorator_types
    }
    interpretation_args = {
        key: value for key, value in kwargs.items() if key not in decorators
    }

    return decorators, interpretation_args


class Interpretation(ABC):
    """An Interpretation is the encapsulation of a single perspective on the data being interpreted.

    In other words, the responsibility of an interpretation is to add additional data to a `DesiredIngest` in the form
    of information about the source node, or relationships in or out of it.
    """

    @classmethod
    def from_type(cls, type: str, **kwargs):
        decorators, interpretation_args = _decompose_args(kwargs)
        interpretation = _interpretation_types[type](**interpretation_args)
        for decorator_name, decorator_args in decorators.items():
            decorator_class = _interpretation_decorator_types[decorator_name]
            interpretation = decorator_class(interpretation, **decorator_args)
        return interpretation

    def __init_subclass__(cls, type, decorator=False) -> None:
        if decorator:
            _interpretation_decorator_types[type] = cls
        else:
            _interpretation_types[type] = cls

    def search_for_single_value(self, search_subject, search_pattern, desired_ingest):
        # If we were given a static value or a search, just return that value
        if isinstance(search_pattern, GlobalVariableLoader):
            return desired_ingest.global_var.get(search_pattern.variable_name)

        if not isinstance(search_pattern, ParsedResult):
            return search_pattern

        result = search_pattern.search(search_subject)
        if result is None:
            return None
        if isinstance(result, list):
            if len(result) > 0:
                result = result[0]
            else:
                return None

        is_string_ending_with_dot = isinstance(result, str) and result.endswith(".")
        return result[:-1] if is_string_ending_with_dot else result

    def search_for_many_values(self, search_subject, search_pattern):
        result = search_pattern.search(search_subject) or []
        return result if isinstance(result, list) else [result]

    @deduplicate_returned_list
    def search_for_many_values_without_trailing_dots(
        self, search_subject, search_pattern
    ):
        results = self.search_for_many_values(search_subject, search_pattern)
        return [result[:-1] if result.endswith(".") else result for result in results]

    @deduplicate_returned_list
    def search_many_search_patterns_for_values_without_trailing_dots(
        self, search_subject, search_patterns
    ):
        search_patterns = (
            search_patterns if isinstance(search_patterns, list) else [search_patterns]
        )
        return [
            result
            for search_pattern in search_patterns
            for result in self.search_for_many_values_without_trailing_dots(
                search_subject, search_pattern
            )
        ]

    def apply_searches_as_metadata(
        self, data, metadata_object, desired_ingest, **searches
    ):
        for key, search_pattern in searches.items():
            search_value = self.search_for_single_value(
                data, search_pattern, desired_ingest
            )
            if search_value is not None:
                metadata_object.add_metadata(key, search_value)

    def apply_searches_as_global_var(
        self, data, global_var_object, desired_ingest, **searches
    ):
        for key, search_pattern in searches.items():
            search_value = self.search_for_single_value(
                data, search_pattern, desired_ingest
            )
            if search_value is not None:
                global_var_object.add_global_var(key, search_value)

    @abstractmethod
    def interpret(self, data: JsonDocument, desired_ingest: DesiredIngestion):
        raise NotImplementedError

    def gather_used_indices(self):
        yield from []
