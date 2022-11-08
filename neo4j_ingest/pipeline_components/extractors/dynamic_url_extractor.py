from etwpipeline import Extractor
from etwpipeline.contrib.http_utils import resilient_session_factory


class DynamicUrlExtractor(Extractor):
    def __init__(self, dynamic_url: str, yield_from: str):
        self.dynamic_url = dynamic_url
        self.yield_from = yield_from
        self.session = resilient_session_factory()

    def extract_records(self):
        yield from self.session.get(self.dynamic_url).json()[self.yield_from]
