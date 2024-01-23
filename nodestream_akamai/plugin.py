from nodestream.project import Project, ProjectPlugin


class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        project.add_plugin_scope_from_pipeline_resources(
            name="akamai", package="nodestream_akamai"
        )
