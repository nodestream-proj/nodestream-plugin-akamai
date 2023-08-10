import re
from glob import glob
from logging import getLogger
from threading import Lock
from typing import List, Optional

from .pipeline_worker import PipelineJob, PipelineWorker
from .worker_group import WorkerGroup
from nodestream.pipeline.class_loader import PipelineJob, PipelineWorker


class WorkerLoader:
    def __init__(self, pipeline_directory: str, scope: Optional[str] = None):
        self.pipeline_directory = pipeline_directory
        self.scope_regex = scope
        self.logger = getLogger(self.__class__.__name__)

    def find_pipeline_files(self):
        directory_search = glob(f"{self.pipeline_directory}/*.yaml")
        return (
            file
            for file in directory_search
            if self.scope_regex is None or re.search(self.scope_regex, file)
        )

    def make_worker(self, pipeline_file, lock):
        
        return PipelineWorker(PipelineJob.from_file(pipeline_file, lock))

    def load_workers(self) -> List[PipelineWorker]:
        lock = Lock()
        return [
            self.make_worker(pipeline_file, lock)
            for pipeline_file in self.find_pipeline_files()
        ]

    def load_worker_group(self):
        workers = self.load_workers()
        self.logger.info("Booting Worker Group of size: %d", len(workers))
        return WorkerGroup(workers)
