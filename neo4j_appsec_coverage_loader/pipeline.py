from etwpipeline import Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("neo4j_appsec_coverage_loader/akamai-appsec-coverage.yaml")
