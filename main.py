import logging
import os

import akamai_property_cacher, akamai_redirect_cacher, neo4j_property_loader, neo4j_redirect_loader

SELECTED_PIPELINES = os.environ["SELECTED_PIPELINES"].split(",")
PIPELINE_FACTORIES = {
    "akamai_property_cacher": akamai_property_cacher.make_pipeline,
    "akamai_redirect_cacher": akamai_redirect_cacher.make_pipeline,
    "neo4j_property_loader": neo4j_property_loader.make_pipeline,
    "neo4j_redirect_loader": neo4j_redirect_loader.make_pipeline,
}


def main():
    logger = logging.getLogger(__name__)
    for pipeline_name in SELECTED_PIPELINES:
        logger.info("Running Pipeline named: %s", pipeline_name)
        pipeline = PIPELINE_FACTORIES[pipeline_name]()
        pipeline.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
