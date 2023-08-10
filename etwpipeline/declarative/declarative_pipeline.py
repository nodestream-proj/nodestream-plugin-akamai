# from ..pipeline import Pipeline, PipelineExtractor
# from .exceptions import InvalidPipelineDefinitionError
# from nodestream.pipeline import PipelineFileLoader
# from .resolvers import ArgumentResolvers

# from nodestream.pipeline import ClassLoader

# def _load_optional_list(class_loader, class_data_list):
#     return [class_loader.load_class(**class_data) for class_data in class_data_list]


# DEFAULT_PIPELINE_IMPLEMENTATION = "etwpipeline:Pipeline"
# OPTIONAL_LIST_ARGUMENT_NAMES = [
#     "pre_transform_filters",
#     "post_transform_filters",
#     "writers",
#     "transformers",
# ]


# class DeclarativePipeline(Pipeline):
#     @classmethod
#     def load_extractor(cls, class_loader, extractor_data, upstream_pipeline):
#         if upstream_pipeline is not None:
#             if extractor_data is not None:
#                 raise InvalidPipelineDefinitionError(
#                     "extractor data must not be provided when using upstream pipeline",
#                     extractor_data,
#                 )
#             return PipelineExtractor(upstream_pipeline)
#         return (
#             None
#             if extractor_data is None
#             else class_loader.load_class(**extractor_data)
#         )

#     @classmethod
#     def from_single_pipeline_definiton(cls, pipeline_data, upstream_pipeline=None):
#         class_loader = ClassLoader(
#             ArgumentResolvers.from_resolver_data(pipeline_data.pop("resolvers", []))
#         )
#         extractor = cls.load_extractor(
#             class_loader, pipeline_data.pop("extractor", None), upstream_pipeline
#         )

#         optional_list_arguments = {
#             key: _load_optional_list(class_loader, pipeline_data.pop(key, []))
#             for key in OPTIONAL_LIST_ARGUMENT_NAMES
#         }

#         pipeline_implementation = pipeline_data.pop(
#             "implementation", DEFAULT_PIPELINE_IMPLEMENTATION
#         )
#         return class_loader.load_class(
#             implementation=pipeline_implementation,
#             arguments=dict(
#                 extractor=extractor, **optional_list_arguments, **pipeline_data
#             ),
#         )

#     @classmethod
#     def from_object_definition(cls, file_data) -> Pipeline:
#         if isinstance(file_data, dict):
#             return cls.from_single_pipeline_definiton(file_data)
#         if not isinstance(file_data, list):
#             raise InvalidPipelineDefinitionError(
#                 "Declarative pipeline data must be array or dict", type(file_data)
#             )
#         pipeline = None
#         for pipeline_data in file_data:
#             pipeline = cls.from_single_pipeline_definiton(pipeline_data, pipeline)
#         return pipeline

#     @classmethod
#     def from_file(cls, file_name) -> Pipeline:
#         file_data = PipelineFileLoader.for_file(file_name).load_data()
#         return cls.from_object_definition(file_data)
