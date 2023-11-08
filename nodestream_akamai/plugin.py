from nodestream.project import Project, ProjectPlugin, PipelineScope

class AkamaiPlugin(ProjectPlugin):
    def activate(self, project: Project) -> None:
            scope = PipelineScope.from_resources(name="akamai", package="nodestream_akamai")
            project.add_scope(scope),