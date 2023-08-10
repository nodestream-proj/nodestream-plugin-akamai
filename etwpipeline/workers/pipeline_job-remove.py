from logging import getLogger
from os.path import splitext
from threading import Lock
from time import sleep
from typing import Optional

# from .pipeline_file import PipelineFile
from nodestream.pipeline import PipelineFileLoader
from nodestream.pipeline import Pipeline

UNHANDLED_ERROR_MESSAGE = (
    "Encountered unhandled exception in pipeline. Restarting again in 30 seconds."
)


class PipelineJob:
    def __init__(
        self,
        job_name: str,
        pipeline: Pipeline,
        initialization_lock: Optional[Lock] = None,
    ) -> None:
        self.pipeline = pipeline
        self.starts = 0
        self.records_processed = 0
        self.in_error_state = False
        self.terminated = False
        self.logger = getLogger(job_name)
        self.name = job_name
        self.initialization_lock = initialization_lock

    def init_pipeline(self):
        def actually_do_init():
            self.starts += 1
            self.in_error_state = False
            self.terminated = False
            return self.pipeline

        if self.initialization_lock:
            with self.initialization_lock:
                return actually_do_init()

        return actually_do_init()

    def do_job_once(self):
        try:
            for chunk in self.init_pipeline().run_iteratively():
                self.logger.info("Processed chunk of size %d", len(chunk))
                self.records_processed += len(chunk)
        except Exception:
            self.logger.exception(UNHANDLED_ERROR_MESSAGE)
            self.in_error_state = True
        finally:
            self.terminated = True

    def do_job_until_successfully_complete(self):
        should_loop_again = True
        while should_loop_again:
            self.do_job_once()
            should_loop_again = self.in_error_state
            if should_loop_again:
                sleep(30)

    def get_state(self):
        return {
            "name": self.name,
            "starts": self.starts,
            "records_processed": self.records_processed,
            "in_error_state": self.in_error_state,
            "terminated": self.terminated,
        }

    @classmethod
    def from_file(cls, declarative_pipeline_file_name, initialization_lock=None):
        name, _ = splitext(declarative_pipeline_file_name)
        loader = PipelineFileLoader(declarative_pipeline_file_name)
        return cls(name, loader, initialization_lock=initialization_lock)
