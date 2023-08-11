from nodestream.project import Project, ProjectPlugin, PipelineScope

class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        scopes = [
            PipelineScope.from_resources(name="appsec-coverage", package="nodestream_akamai.appsec_coverage"),
            PipelineScope.from_resources(name="cps", package="nodestream_akamai.cps"),
            PipelineScope.from_resources(name="ehn", package="nodestream_akamai.ehn"),
            PipelineScope.from_resources(name="gtm", package="nodestream_akamai.gtm"),
            PipelineScope.from_resources(name="netstorage", package="nodestream_akamai.netstorage"),
            PipelineScope.from_resources(name="propery", package="nodestream_akamai.property"),
            PipelineScope.from_resources(name="redirect", package="nodestream_akamai.redirect"),
            PipelineScope.from_resources(name="siteshield", package="nodestream_akamai.siteshield"),
            PipelineScope.from_resources(name="waf", package="nodestream_akamai.waf"),
        ]
        for scope in scopes:
            project.add_scope(scope)