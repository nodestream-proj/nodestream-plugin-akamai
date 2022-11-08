import argparse
import logging
import sys

from etwpipeline.declarative import DeclarativePipeline


def construct_parser():
    parser = argparse.ArgumentParser(
        description="run etwpipeline on your desired file!"
    )
    parser.add_argument("file", type=str, help="path to your file")
    parser.add_argument(
        "--level", type=str, default="INFO", help="view INFO/WARNING/ERROR level"
    )
    return parser


def run_pipeline(file):
    my_pipeline = DeclarativePipeline.from_file(file)
    my_pipeline.run()


def configure_log_level(input_level):
    level = logging.getLevelName(input_level)
    logging.basicConfig(level=level)


def main(args=sys.argv):
    parser = construct_parser()
    args = parser.parse_args(args[1:])
    configure_log_level(args.level)
    run_pipeline(args.file)


if __name__ == "__main__":
    main()
