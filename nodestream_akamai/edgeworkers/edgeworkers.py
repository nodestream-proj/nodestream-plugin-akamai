import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils.edgeworkers_client import AkamaiEdgeworkersClient


class AkamaiEdgeworkersExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdgeworkersClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_records(self):
        try:
            edgeworkers = self.client.list_edgeworkers()
        except Exception as err:
            self.logger.error("Failed to list edgeworkers: %s", err)

        for edgeworker in edgeworkers:
            active_version = None
            try:
                active_version = self.client.get_production_version(
                    edgeworker["edgeWorkerId"]
                )
            except Exception as err:
                self.logger.error(
                    f"""Failed to get production activation info for EW '{edgeworker["name"]}': {err}"""
                )

            # Add deeplink
            edgeworker[
                "deeplink"
            ] = f'https://control.akamai.com/apps/edgeworkers/#/ids/{edgeworker["edgeWorkerId"]}/versions'

            if active_version is not None:
                edgeworker["activeVersion"] = active_version["version"]

            yield edgeworker
