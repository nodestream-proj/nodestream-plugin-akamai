from etwpipeline import Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("neo4j_netstorage_group_loader/akamai-netstorage-group.yaml")
