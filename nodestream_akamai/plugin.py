from nodestream.project import Project, ProjectPlugin, PipelineScope

class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        scopes = [
            PipelineScope.from_resources(name="akamai_appsec-coverage", package="nodestream_akamai.appsec_coverage"),
            PipelineScope.from_resources(name="akamai_cps", package="nodestream_akamai.cps"),
            PipelineScope.from_resources(name="akamai_ehn", package="nodestream_akamai.ehn"),
            PipelineScope.from_resources(name="akamai_gtm", package="nodestream_akamai.gtm"),
            PipelineScope.from_resources(name="akamai_netstorage_group", package="nodestream_akamai.netstorage_group"),
            PipelineScope.from_resources(name="akamai_netstorage_account", package="nodestream_akamai.netstorage_account"),
            PipelineScope.from_resources(name="akamai_propery", package="nodestream_akamai.property"),
            PipelineScope.from_resources(name="akamai_redirect", package="nodestream_akamai.redirect"),
            PipelineScope.from_resources(name="akamai_siteshield", package="nodestream_akamai.siteshield"),
            PipelineScope.from_resources(name="akamai_waf", package="nodestream_akamai.waf"),
        ]
        for scope in scopes:
            project.add_scope(scope)