# class InvalidClassPathError(ValueError):
#     pass


# class InvalidPipelineDefinitionError(ValueError):
#     pass


# class InvalidPipelineFileError(ValueError):
#     pass


# class PipelineComponentInitilizationError(ValueError):
#     def __init__(self, initializier, init_arguments, *args: object) -> None:
#         super().__init__(
#             "Failed to Initialize Component in Declarative Pipeline.", *args
#         )
#         self.initializier = initializier
#         self.init_arguments = init_arguments
