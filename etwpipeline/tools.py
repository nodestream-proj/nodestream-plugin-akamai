import csv
import json

from etwpipeline import Extractor


class FixtureFileExtractor(Extractor):
    def __init__(self, files) -> None:
        self.file_names = files

    def extract_records(self):
        for file_name in self.file_names:
            with open(file_name) as fp:
                if file_name.endswith("csv"):
                    yield from csv.DictReader(fp)
                else:
                    yield from json.load(fp)
