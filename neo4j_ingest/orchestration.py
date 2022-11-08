import os
from logging import getLogger
from pathlib import Path
from threading import current_thread
from typing import List, Optional

import jmespath
from etwpipeline.declarative.file_loaders import YamlFileLoader
from etwpipeline.workers import PipelineFile
from yaml import SafeLoader, safe_load

DEFAULT_REGISTRY_LOCATION = "pipelines/registry.yaml"


SafeLoader.add_constructor(
    "tag:yaml.org,2002:python/jmespath",
    lambda l, n: jmespath.compile(l.construct_scalar(n)),
)

SafeLoader.add_constructor(
    "tag:yaml.org,2002:global_variable",
    lambda l, n: GlobalVariableLoader(l.construct_scalar(n)),
)


class GlobalVariableLoader:
    def __init__(self, variable_name: str) -> None:
        self.variable_name = variable_name


def get_default_pipeline_name(definition):
    return Path(definition).stem


class CustomYamlFileLoader(YamlFileLoader, extension=".yaml"):
    def is_test_environment(self):
        return "APP_ENV" not in os.environ

    def load_data_from_file_pointer(self, fp):
        data = super().load_data_from_file_pointer(fp)
        if self.is_test_environment() and "extractor" in data:
            data["extractor"] = data.pop("test_extractor", data["extractor"])

        if "test_extractor" in data:
            data.pop("test_extractor")

        return data


class PipelineConfiguration:
    """Defines a single pipeline. Defines desired concurrency, name, and definition."""

    def __init__(
        self,
        definition: str,
        name: Optional[str] = None,
        concurrency: Optional[int] = None,
        schedule: Optional[str] = None,
    ) -> None:
        self.definition = PipelineFile(definition)
        self.concurrency = concurrency or 1
        self.name = name or get_default_pipeline_name(definition)
        self.logger = getLogger(self.__class__.__name__)
        self.schedule = schedule

    def as_json(self):
        return {
            "name": self.name,
            "concurrency": self.concurrency,
            "definition": self.definition.declarative_pipeline_file_name,
            "schedule": self.schedule,
        }

    def execute(self):
        current_thread().name = self.name
        for chunk in self.definition.as_pipeline().run_iteratively():
            self.logger.info(
                "Processed chunk", extra={"size": len(chunk), "pipeline": self.name}
            )


class PipelineScope:
    """Defines a scope of pipelines. Essentially a logical group of related pipelines."""

    @classmethod
    def from_file_data(cls, file_data):
        pipelines = [
            PipelineConfiguration(**pipeline) for pipeline in file_data["pipelines"]
        ]
        return cls(file_data["name"], pipelines)

    def __init__(self, name: str, pipelines: List[PipelineConfiguration]) -> None:
        self.name = name
        self.pipelines = {pipeline.name: pipeline for pipeline in pipelines}

    def __iter__(self):
        return iter(self.pipelines.values())

    def __getitem__(self, pipeline_name):
        return self.pipelines[pipeline_name]

    def __contains__(self, pipeline_name):
        return pipeline_name in self.pipelines


class PipelineRegistry:
    """Manages the model for the registry.yaml file.

    This class stores all scopes and pipelines and provides the High level API for executing and querying for pipelines.
    """

    @classmethod
    def instance(cls):
        with open(DEFAULT_REGISTRY_LOCATION) as fp:
            data = safe_load(fp)

        scopes = [PipelineScope.from_file_data(scope) for scope in data["scopes"]]
        return PipelineRegistry(scopes)

    def __init__(self, scopes: List[PipelineScope]) -> None:
        self.scopes = {scope.name: scope for scope in scopes}
        self.logger = getLogger(self.__class__.__name__)

    def run_pipeline(self, target):
        for scope in self.scopes.values():
            self.logger.info(
                "Finding matching targets in scope",
                extra=dict(target=target, scope=scope.name),
            )
            if target in scope:
                pipeline = scope[target]
                self.logger.info(
                    "Found matching pipeline", extra=dict(pipeline=pipeline.as_json())
                )
                pipeline.execute()

        self.logger.info("Found no additional matching pipelines")

    def get_all_pipelines(self, scope=None):
        scopes = [self.scopes[scope]] if scope else self.scopes.values()
        return [pipeline for scope in scopes for pipeline in scope]
