import json
import os
import re
import jmespath
from abc import ABC, abstractmethod

from .exceptions import InvalidPipelineFileError
from nodestream.file_io import LoadsFromJsonFile, LoadsFromYamlFile


_registry = {}


# class FileLoader(ABC):
#     def __init__(self, file_name):
#         self.file_name = file_name

#     def __init_subclass__(cls, extension=None):
#         _registry[extension] = cls

#     @abstractmethod
#     def load_data_from_file_pointer(self, fp):
#         raise NotImplementedError

#     def load_data(self):
#         try:
#             with open(self.file_name) as fp:
#                 return self.load_data_from_file_pointer(fp)
#         except FileNotFoundError as e:
#             raise InvalidPipelineFileError(
#                 f"The file '{self.file_name}' was not found on disk."
#             ) from e
#         except PermissionError as e:
#             raise InvalidPipelineFileError(
#                 f"The file '{self.file_name}' cannot be read by the current user."
#             ) from e

#     @classmethod
#     def for_file(cls, file_name):
#         _, extension = os.path.splitext(file_name)
#         try:
#             return _registry[extension](file_name)
#         except KeyError as e:
#             raise InvalidPipelineFileError(
#                 f"File of type '{extension}' does not have a registered FileLoader."
#             ) from e


# # JSON file loaders are always available because json loading is part of the standard library.
# class JsonFileLoader(FileLoader, extension=".json"):
#     def load_data_from_file_pointer(self, fp):
#         return json.load(fp)


# # In order to support loading from yaml files, you must have the "yaml" extra installed.
# try:
#     from yaml import SafeLoader, safe_load

#     def include_file(loader, node):
#         file_dir = os.path.split(loader.stream.name)[0]
#         file_name = os.path.join(file_dir, loader.construct_scalar(node))
#         return FileLoader.for_file(file_name).load_data()

#     def add_custom_class_loaders():
#         SafeLoader.add_constructor("!include", include_file)
#         SafeLoader.add_constructor(
#             "tag:yaml.org,2002:python/regexp",
#             lambda l, n: re.compile(l.construct_scalar(n)),
#         )
#         SafeLoader.add_constructor(
#             "tag:yaml.org,2002:python/jmespath",
#             lambda l, n: jmespath.compile(l.construct_scalar(n)),
#         )

#     add_custom_class_loaders()

#     class YamlFileLoader(FileLoader, extension=".yaml"):
#         def load_data_from_file_pointer(self, fp):
#             return safe_load(fp)

# except ImportError:
#     pass


# # In order to support loading from toml files, you must have the "toml" extra installed.
# try:
#     from toml import load

#     class TomlFileLoader(FileLoader, extension=".toml"):
#         def load_data_from_file_pointer(self, fp):
#             return load(fp)

# except ImportError:
#     pass
