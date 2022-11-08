from importlib import import_module

from .exceptions import InvalidClassPathError, PipelineComponentInitilizationError
from .resolvers import ArgumentResolvers

DECLARATIVE_INIT_METHOD_NAME = "__declarative_init__"


class ClassLoader:
    def __init__(self, resolvers: ArgumentResolvers):
        self.resolvers = resolvers

    def find_class(self, class_path):
        try:
            module_name, class_name = class_path.split(":")
            module = import_module(module_name)
            return getattr(module, class_name)
        except ValueError as e:
            raise InvalidClassPathError(
                f"Class path '{class_path}' is not in the correct format."
            ) from e
        except ImportError as e:
            raise InvalidClassPathError(
                f"Module '{module_name}' could not be imported."
            ) from e
        except AttributeError as e:
            raise InvalidClassPathError(
                f"Class '{class_name}' does not exist in module '{module_name}'."
            ) from e

    def find_class_initializer(self, implementation, factory=None):
        class_definition = self.find_class(implementation)
        factory_method = factory or DECLARATIVE_INIT_METHOD_NAME

        if hasattr(class_definition, factory_method):
            return getattr(class_definition, factory_method)
        else:
            return class_definition

    def resolve_arguments(self, arguments):
        return self.resolvers.resolve_arguments(arguments)

    def load_class(self, implementation, arguments=None, factory=None):
        arguments = arguments or {}
        resolved_args = self.resolve_arguments(arguments)
        initializier = self.find_class_initializer(implementation, factory)
        try:
            return initializier(**resolved_args)
        except TypeError as e:
            raise PipelineComponentInitilizationError(
                initializier, resolved_args
            ) from e
