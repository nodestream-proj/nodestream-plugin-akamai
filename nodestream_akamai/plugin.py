from nodestream.project import PipelineScope, Project, ProjectPlugin


class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
        scope = PipelineScope.from_resources(name="akamai", package="nodestream_akamai")
        project.add_scope(scope),
