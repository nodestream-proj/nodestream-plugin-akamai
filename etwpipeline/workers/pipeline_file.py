from etwpipeline.declarative import DeclarativePipeline


class PipelineFile:
    def __init__(self, declarative_pipeline_file_name: str) -> None:
        self.declarative_pipeline_file_name = declarative_pipeline_file_name

    def as_pipeline(self):
        return DeclarativePipeline.from_file(self.declarative_pipeline_file_name)
