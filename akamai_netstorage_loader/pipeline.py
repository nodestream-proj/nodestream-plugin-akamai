from etwpipeline import Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_netstorage_loader/akamai-netstorage.yaml")
