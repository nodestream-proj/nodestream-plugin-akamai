from nodestream.project import Project, ProjectPlugin, PipelineScope, PipelineDefinition

class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        scopes = [
            PipelineScope.from_resources(name="appsec-coverage-cacher", package="nodestream_akamai.appsec_coverage"),
            PipelineScope.from_resources(name="appsec-coverage-loader", package="nodestream_akamai.appsec_coverage"),
            PipelineScope.from_resources(name="cps-cacher", package="nodestream_akamai.cps"),
            PipelineScope.from_resources(name="cps-loader", package="nodestream_akamai.cps"),
            PipelineScope.from_resources(name="ehn-cacher", package="nodestream_akamai.ehn"),
            PipelineScope.from_resources(name="ehn-loader", package="nodestream_akamai.ehn"),
            PipelineScope.from_resources(name="gtm-cacher", package="nodestream_akamai.gtm"),
            PipelineScope.from_resources(name="gtm-loader", package="nodestream_akamai.gtm"),
            PipelineScope.from_resources(name="netstorage-cacher", package="nodestream_akamai.netstorage"),
            PipelineScope.from_resources(name="netstorage-loader", package="nodestream_akamai.netstorage"),
            PipelineScope.from_resources(name="propery-cacher", package="nodestream_akamai.property"),
            PipelineScope.from_resources(name="property-loader", package="nodestream_akamai.property"),
            PipelineScope.from_resources(name="redirect-cacher", package="nodestream_akamai.redirect"),
            PipelineScope.from_resources(name="redirect-loader", package="nodestream_akamai.redirect"),
            PipelineScope.from_resources(name="siteshield-cacher", package="nodestream_akamai.siteshield"),
            PipelineScope.from_resources(name="siteshield-loader", package="nodestream_akamai.siteshield"),
            PipelineScope.from_resources(name="waf-cacher", package="nodestream_akamai.waf"),
            PipelineScope.from_resources(name="waf-loader", package="nodestream_akamai.waf"),
        ]
        for scope in scopes:
            project.add_scope(scope)