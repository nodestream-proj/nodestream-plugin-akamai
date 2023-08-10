# import json
# import os
# from abc import ABC, abstractmethod
# from functools import lru_cache
# from nodestream.pipeline.extractors import AWSClientFactory

# _argument_resolver_registry = {}
# _type_resolution_strategy_registry = {}

# PREFIX_DELIMITER = "://"


# class ArgumentResolver(ABC):
#     def __init_subclass__(cls, prefix=None):
#         super().__init_subclass__()
#         cls.prefix = prefix
#         _argument_resolver_registry[prefix] = cls

#     @abstractmethod
#     def resolve_argument(self, raw_value_sans_prefix):
#         raise NotImplementedError


# class RawValueResolver(ArgumentResolver, prefix=None):
#     def __init__(self, re_append_prefix=None) -> None:
#         self.re_append_prefix = re_append_prefix

#     def resolve_argument(self, raw_value_sans_prefix):
#         # If we are executing a `RawValueResolver` in the case where there
#         # was a prefix that we do not handle, we need to rebuild the original
#         # value by gluing the prefix back on to the front with the delimeter.
#         if self.re_append_prefix is not None:
#             return f"{self.re_append_prefix}{PREFIX_DELIMITER}{raw_value_sans_prefix}"
#         return raw_value_sans_prefix


# class EnvironmentResolver(ArgumentResolver, prefix="env"):
#     def resolve_argument(self, raw_value_sans_prefix):
#         return os.environ.get(raw_value_sans_prefix)


# try:
#     from nodestream.pipeline.extractors import AWSClientFactory

#     class SecretsManagerResolver(ArgumentResolver, prefix="secrets_manager"):
#         def __init__(
#             self,
#             assume_role_arn=None,
#             assume_role_external_id=None,
#             **boto_extra_args,
#         ):
#             aws_factory = AWSClientFactory(
#                 assume_role_arn, assume_role_external_id, **boto_extra_args
#             )

#             self.secretsmanager = aws_factory.make_client("secretsmanager")

#         @lru_cache
#         def get_secret(self, secret_key):
#             return self.secretsmanager.get_secret_value(SecretId=secret_key)[
#                 "SecretString"
#             ]

#         def resolve_argument(self, raw_value_sans_prefix):
#             splits = raw_value_sans_prefix.split(":", 1)
#             if len(splits) == 2:
#                 secret_key, field_name = splits
#             else:
#                 secret_key, field_name = raw_value_sans_prefix, None

#             secret_value = self.get_secret(secret_key)
#             if field_name is not None:
#                 return json.loads(secret_value)[field_name]
#             else:
#                 return secret_value

# except ImportError:
#     pass


# except ImportError:
#     pass


# class TypeResolutionStrategy:
#     @classmethod
#     def for_type(cls, type):
#         return _type_resolution_strategy_registry.get(
#             type, DefaultTypeResolutionStrategy
#         )()

#     def __init_subclass__(cls, type=None) -> None:
#         _type_resolution_strategy_registry[type] = cls


# class DefaultTypeResolutionStrategy(TypeResolutionStrategy, type=None):
#     def resolve(self, _, raw_value):
#         return raw_value


# class StringTypeResolutionStrategy(TypeResolutionStrategy, type=str):
#     def parse_components(self, raw_value):
#         splits = raw_value.split(PREFIX_DELIMITER, 1)
#         if len(splits) == 2:
#             return splits
#         else:
#             return None, raw_value

#     def resolve(self, resolvers, raw_value):
#         prefix, raw_value_sans_prefix = self.parse_components(raw_value)
#         return resolvers.resolver_for(prefix).resolve_argument(raw_value_sans_prefix)


# class ListTypeResolutionStrategy(TypeResolutionStrategy, type=list):
#     def resolve(self, resolvers, raw_value):
#         return [resolvers.resolve_argument(item) for item in raw_value]


# class DictionaryTypeResolutionStrategy(TypeResolutionStrategy, type=dict):
#     def resolve(self, resolvers, raw_value):
#         return resolvers.resolve_arguments(raw_value)


# class ArgumentResolvers:
#     @classmethod
#     def from_resolver_data(cls, resolvers_data):
#         from nodestream.pipeline import ClassLoader

#         current_resolvers = []
#         arg_resolver = ArgumentResolvers(current_resolvers)
#         class_loader = ClassLoader(arg_resolver)
#         for resolver_data in resolvers_data:
#             current_resolvers.append(class_loader.load_class(**resolver_data))
#         return arg_resolver

#     def __init__(self, resolvers):
#         self.resolvers = resolvers

#     def resolver_for(self, prefix):
#         for resolver in self.resolvers:
#             if resolver.prefix == prefix:
#                 return resolver

#         return RawValueResolver(re_append_prefix=prefix)

#     def resolve_argument(self, raw_value):
#         value_type = type(raw_value)
#         return TypeResolutionStrategy.for_type(value_type).resolve(self, raw_value)

#     def resolve_arguments(self, arguments):
#         return {
#             key: self.resolve_argument(raw_value)
#             for key, raw_value in arguments.items()
#         }
