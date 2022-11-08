from collections import deque
from copy import copy
from functools import reduce
from typing import Any, Iterable, List, Optional

from .extractors import EmptyExtractor, Extractor, Flush
from .filters import Filter
from .join import Join, JoinStrategy
from .resiliency import attempt
from .transformers import Transformer
from .writers import Writer


def _first_defined_value(*options):
    return next(option for option in options if option is not None)


def take_while_index(predicate, iterable):
    for i, value in enumerate(iterable):
        if not predicate(i):
            break

        yield value


class Pipeline:
    """`Pipeline` encapsulates the various compontents of a data flow and mediates between them."""

    def __init__(
        self,
        extractor: Optional[Extractor] = None,
        pre_transform_filters: Optional[Iterable[Filter]] = None,
        post_transform_filters: Optional[Iterable[Filter]] = None,
        transformers: Optional[Iterable[Transformer]] = None,
        writers: Optional[Iterable[Writer]] = None,
        write_batch_sizes: int = 10,
        extract_limit: Optional[int] = None,
        retry_times: int = 3,
        retry_backoff: int = 0,
        transform_retry_times: Optional[int] = None,
        transform_retry_backoff: Optional[int] = None,
        writer_retry_times: Optional[int] = None,
        writer_retry_backoff: Optional[int] = None,
    ) -> None:
        """Initializes a new pipeline.

        Args:
            extractor: (optional) An instance of Extractor that will act as the data source.
            filters: (optional) A list of instances of Filter. Filters are called for each item produced by the `extractor`.
            transformers: (optional) A list of transformers for your data. Each transformer will be called in order with the output of the previous passed to the next.
            writers: (optional) A list writers where records will be written to after being transformed.
            write_batch_sizes: (optional) The size of batches that will be transformed and written together. This will be treated as a maximum and not always met.
            extract_limit: The maximum number of records to read from extractor. Specifically for extractors.
            retry_times: (optional) The default amount of times to try to execute a step in the pipeline. Subsumed by `writer_retry_times` and `transform_retry_times`.
            retry_backoff: (optional) The default amount of time (in seconds) added to the wait time before retrying. Subsumed by `writer_retry_backoff` and `transform_retry_backoff`.
            transform_retry_times: The default amount of times to try to execute a step in the pipeline. Specifically for transformers. Overrides `retry_times`.
            transform_retry_backoff: The default amount of time (in seconds) added to the wait time before retrying. Specifically for transformers. Overrides `retry_backoff`.
            writer_retry_times: The default amount of times to try to execute a step in the pipeline. Specifically for writers.  Overrides `retry_times`.
            writer_retry_backoff: The default amount of time (in seconds) added to the wait time before retrying. Specifically for writers. Overrides `retry_backoff`.
        """
        self.extractor = EmptyExtractor() if extractor is None else extractor
        self.transformers = [] if transformers is None else transformers
        self.writers = [] if writers is None else writers
        self.pre_transform_filters = (
            [] if pre_transform_filters is None else pre_transform_filters
        )
        self.post_transform_filters = (
            [] if post_transform_filters is None else post_transform_filters
        )
        self.write_batch_sizes = write_batch_sizes
        self.extract_limit = extract_limit

        self.transform_retry_times = _first_defined_value(
            transform_retry_times, retry_times
        )
        self.transform_retry_backoff = _first_defined_value(
            transform_retry_backoff, retry_backoff
        )
        self.writer_retry_times = _first_defined_value(writer_retry_times, retry_times)
        self.writer_retry_backoff = _first_defined_value(
            writer_retry_backoff, retry_backoff
        )

        wrap_transformer = attempt(
            times=self.transform_retry_times, backoff=self.transform_retry_backoff
        )
        self.wrapped_transformers = [
            wrap_transformer(transformer.transform) for transformer in self.transformers
        ]

        wrap_writer = attempt(
            times=self.writer_retry_times, backoff=self.writer_retry_backoff
        )
        self.wrapped_batch_writes = [
            wrap_writer(writer.batch_write) for writer in self.writers
        ]

        self.steps = [
            *self.pre_transform_filters,
            *self.transformers,
            *self.post_transform_filters,
        ]

    def flush(self, items: List[Any]):
        for batch_write in self.wrapped_batch_writes:
            batch_write(items)

    def records(self):
        extracted_records = take_while_index(
            lambda i: self.extract_limit is None or i < self.extract_limit,
            self.extractor.extract_records(),
        )
        # Start with the records from the extractor.
        # feed it through each step in the chain.
        return reduce(
            lambda current, next: next.perform_step_over_generator(current),
            self.steps,
            extracted_records,
        )

    def record_chunks(self):
        current_chunk = []

        for item in self.records():
            if item is Flush:
                should_yield = len(current_chunk) > 0
            else:
                current_chunk.append(item)
                should_yield = len(current_chunk) == self.write_batch_sizes

            if should_yield:
                yield current_chunk
                current_chunk = []

        if len(current_chunk) > 0:
            yield current_chunk

    def run(self):
        """Drives the pipeline to completion and returns once the entire pipeline is exhausted."""
        # Exhausts the items while not storing the results.
        deque(self.run_iteratively(), maxlen=0)

    def run_iteratively(self):
        """`run_iteratively` transforms and writes chunks of data from the extractor, and then `yields` them to the caller.

        This is mostly used to add "out of pipeline logic". If you simply want to have the pipeline run to exhaustion, simply use `run`.

        ```python
        pipeline = Pipeline() # Init this however.
        for chunk in pipeline.run_iteratively():
            print("processed a chunk of size:", len(chunk))
        ```
        """
        for chunk in self.record_chunks():
            self.flush(chunk)
            yield chunk
        for writer in self.writers:
            writer.finish()

    def daisy_chain_to(self, other: "Pipeline"):
        """Given another pipeline, after records are flushed through this pipeline, will be submitted as input to the other pipeline.

        Args:
            other: The other pipeline to daisy-chain to.
        """
        result = copy(other)
        result.extractor = PipelineExtractor(self)
        return result

    def join_to(
        self, right_side: "Pipeline", on: str, method: str = "inner", **pipeline_args
    ):
        """Performs a SQL-Like join of to distict pipelines on a single key.

        Calling this will return a new `Pipeline` whose extractor will produce the joined records from both sides based on
        the `method` and `on` parameters.

        In order to accomplish this, both pipelines that are being joined must have the following criteria met:

        - Operates on objects that conform to [Python's Mapping Type API](https://docs.python.org/3/library/stdtypes.html#typesmapping) e.g, it needs to be a `dict`
        - The data sets are small enough that both can be fully loaded into memory.

        ```python
        left_extractor = IterableExtractor([{"id": 1, "foo": "bar"} , {"id": 2, "foo": "baz"}, {"id": 3, "foo": "xzy"}])
        right_extractor = IterableExtractor([{"id": 1, "bar": "123"} , {"id": 4, "abc": "123"}])
        left_pipeline = Pipeline(extractor=left_extractor)
        right_pipeline = Pipeline(extractor=right_extractor)

        # ** Inner Join **
        left_pipeline.join_to(right_pipeline, writers=[LoggerWriter()], on="id", method="inner").run()
        # INFO:LoggerWriter:{'id': 1, 'foo': 'bar', 'bar': '123'}

        # ** Left Join **
        left_pipeline.join_to(right_pipeline, writers=[LoggerWriter()], on="id", method="left").run()
        # INFO:LoggerWriter:{'id': 2, 'foo': 'baz'}
        # INFO:LoggerWriter:{'id': 3, 'foo': 'xzy'}
        # INFO:LoggerWriter:{'id': 1, 'foo': 'bar', 'bar': '123'}

        # ** Right Join **
        left_pipeline.join_to(right_pipeline, writers=[LoggerWriter()], on="id", method="right").run()
        # INFO:LoggerWriter:{'id': 1, 'foo': 'bar', 'bar': '123'}
        # INFO:LoggerWriter:{'id': 4, 'abc': '123'}

        # ** Full Outer Join **
        left_pipeline.join_to(right_pipeline, writers=[LoggerWriter()], on="id", method="full").run()
        # INFO:LoggerWriter:{'id': 2, 'foo': 'baz'}
        # INFO:LoggerWriter:{'id': 3, 'foo': 'xzy'}
        # INFO:LoggerWriter:{'id': 1, 'foo': 'bar', 'bar': '123'}
        # INFO:LoggerWriter:{'id': 4, 'abc': '123'}
        ```

        Args:
            right_side: The other pipeline to join records to.
            on: The key to use to join records on from both pipelines.
            method: (optional) One of "inner", "left", "right", and "outer". These follow similar behaviors to their SQL counterparts.
            pipeline_args: Additional keyword argumetns to pass to the resultant pipeline such as writers, transformers.
        """

        def exhaust_pipeline(ppl):
            for chunk in ppl.run_iteratively():
                yield from chunk

        join_strategy = JoinStrategy.by_name(method)
        join = Join(
            exhaust_pipeline(self), exhaust_pipeline(right_side), join_strategy, on
        )
        return Pipeline(extractor=join, **pipeline_args)


class PipelineExtractor(Extractor):
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def extract_records(self):
        for chunk in self.pipeline.run_iteratively():
            yield from chunk
