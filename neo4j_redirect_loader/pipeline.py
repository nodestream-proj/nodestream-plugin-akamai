import logging

from etwpipeline import Extractor, Pipeline
from etwpipeline.declarative import DeclarativePipeline


def make_pipeline() -> Pipeline:
    return DeclarativePipeline.from_file("neo4j_redirect_loader/akamai-redirect-policy.yaml")
