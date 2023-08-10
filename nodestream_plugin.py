from nodestream.project import Project, ProjectPlugin, PipelineScope, PipelineDefinition

class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        scopes = [
            PipelineScope.from_resources(name="appsec-coverage-cacher", package="nodestream-akamai.appsec_coverage"),
            PipelineScope.from_resources(name="appsec-coverage-loader", package="nodestream-akamai.appsec_coverage"),
            PipelineScope.from_resources(name="cps-cacher", package="nodestream-akamai.cps"),
            PipelineScope.from_resources(name="cps-loader", package="nodestream-akamai.cps"),
            PipelineScope.from_resources(name="ehn-cacher", package="nodestream-akamai.ehn"),
            PipelineScope.from_resources(name="ehn-loader", package="nodestream-akamai.ehn"),
            PipelineScope.from_resources(name="gtm-cacher", package="nodestream-akamai.gtm"),
            PipelineScope.from_resources(name="gtm-loader", package="nodestream-akamai.gtm"),
            PipelineScope.from_resources(name="netstorage-cacher", package="nodestream-akamai.netstorage"),
            PipelineScope.from_resources(name="netstorage-loader", package="nodestream-akamai.netstorage"),
            PipelineScope.from_resources(name="propery-cacher", package="nodestream-akamai.property"),
            PipelineScope.from_resources(name="property-loader", package="nodestream-akamai.property"),
            PipelineScope.from_resources(name="redirect-cacher", package="nodestream-akamai.redirect"),
            PipelineScope.from_resources(name="redirect-loader", package="nodestream-akamai.redirect"),
            PipelineScope.from_resources(name="siteshield-cacher", package="nodestream-akamai.siteshield"),
            PipelineScope.from_resources(name="siteshield-loader", package="nodestream-akamai.siteshield"),
            PipelineScope.from_resources(name="waf-cacher", package="nodestream-akamai.waf"),
            PipelineScope.from_resources(name="waf-loader", package="nodestream-akamai.waf"),
        ]
        for scope in scopes:
            project.add_scope(scope)