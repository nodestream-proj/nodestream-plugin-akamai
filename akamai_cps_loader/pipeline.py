from etwpipeline import Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("akamai_cps_loader/akamai-cps.yaml")
