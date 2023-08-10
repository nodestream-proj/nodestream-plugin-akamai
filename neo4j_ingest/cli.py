# import json
# import logging
# import os
# import sys

# import click
# from dotenv import load_dotenv
# from pythonjsonlogger.jsonlogger import JsonFormatter

# from .orchestration import PipelineRegistry

# REGISTRY = PipelineRegistry.instance()


# def configure_profile(profile):
#     if profile is not None:
#         os.environ["APP_ENV"] = profile
#         dot_env_file = f"{profile}.env"
#     else:
#         dot_env_file = ".env"

#     load_dotenv(dot_env_file)


# def _get_logger_level():
#     return os.environ.get("LOG_LEVEL", "INFO")


# def configure_logging():
#     logging.basicConfig(level=_get_logger_level())
#     formatter = JsonFormatter("%(name)s %(message)s", timestamp=True)
#     logger = logging.getLogger()  # Configure the root logger.
#     logger.handlers[0].setFormatter(formatter)


# @click.group()
# @click.option("--profile", default=None, help="Select an .env configuration to load")
# def cli(profile):
#     configure_profile(profile)
#     configure_logging()


# @cli.command()
# @click.option("--scope", default=None, help="Limit to a specified subset.")
# def discover(scope):
#     pipelines_as_json = [p.as_json() for p in REGISTRY.get_all_pipelines(scope)]
#     json.dump(pipelines_as_json, sys.stdout, indent=4, sort_keys=True)


# @cli.command()
# @click.option("--target", default=None, help="Limit to a specified pipeline.")
# def ingest(target):
#     REGISTRY.run_pipeline(target)


# if __name__ == "__main__":
#     cli()
