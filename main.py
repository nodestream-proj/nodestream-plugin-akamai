import logging
import os

#import akamai_property_cacher, akamai_redirect_cacher, akamai_gtm_cacher, akamai_netstorage_cacher, akamai_appsec_cacher, akamai_siteshield_cacher, akamai_waf_cacher, akamai_ehn_cacher, akamai_cps_cacher, neo4j_property_loader, neo4j_redirect_loader, neo4j_gtm_loader, neo4j_netstorage_loader, neo4j_appsec_loader, neo4j_siteshield_loader, neo4j_waf_loader, neo4j_ehn_loader, neo4j_cps_loader
import akamai_property_cacher, akamai_redirect_cacher, akamai_gtm_cacher, akamai_netstorage_cacher, akamai_appsec_cacher, akamai_siteshield_cacher, akamai_waf_cacher, akamai_ehn_cacher, akamai_cps_cacher, neo4j_property_loader, neo4j_redirect_loader, neo4j_gtm_loader, neo4j_netstorage_loader, neo4j_appsec_loader, neo4j_waf_loader, neo4j_ehn_loader, neo4j_cps_loader

SELECTED_PIPELINES = os.environ["SELECTED_PIPELINES"].split(",")
PIPELINE_FACTORIES = {
    "akamai_property_cacher": akamai_property_cacher.make_pipeline,
    "akamai_redirect_cacher": akamai_redirect_cacher.make_pipeline,
    "akamai_gtm_cacher": akamai_gtm_cacher.make_pipeline,
    "akamai_netstorage_cacher": akamai_netstorage_cacher.make_pipeline,
    "akamai_appsec_cacher": akamai_appsec_cacher.make_pipeline,
    "akamai_siteshield_cacher": akamai_siteshield_cacher.make_pipeline,
    "akamai_waf_cacher": akamai_waf_cacher.make_pipeline,
    "akamai_ehn_cacher": akamai_ehn_cacher.make_pipeline,
    "akamai_cps_cacher": akamai_cps_cacher.make_pipeline,
    "neo4j_property_loader": neo4j_property_loader.make_pipeline,
    "neo4j_redirect_loader": neo4j_redirect_loader.make_pipeline,
    "neo4j_gtm_loader": neo4j_gtm_loader.make_pipeline,
    "neo4j_netstorage_loader": neo4j_netstorage_loader.make_pipeline,
    "neo4j_appsec_loader": neo4j_appsec_loader.make_pipeline,
#    "neo4j_siteshield_loader": neo4j_siteshield_loader.make_pipeline,
    "neo4j_waf_loader": neo4j_waf_loader.make_pipeline,
    "neo4j_ehn_loader": neo4j_ehn_loader.make_pipeline,
    "neo4j_cps_loader": neo4j_cps_loader.make_pipeline,
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
