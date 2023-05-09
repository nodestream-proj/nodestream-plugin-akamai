from etwpipeline import Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("neo4j_cps_loader/akamai-cps.yaml")
