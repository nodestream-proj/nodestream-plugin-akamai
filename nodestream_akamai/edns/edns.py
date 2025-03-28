import logging

from nodestream.pipeline.extractors import Extractor

from ..akamai_utils import addresses
from ..akamai_utils.edns_client import AkamaiEdnsClient

SUPPORTED_RECORD_TYPES = [
    "A",
    "AAAA",
    "CNAME",
    "NS",
    "CAA",
]


class AkamaiEdnsExtractor(Extractor):
    def __init__(self, **akamai_client_kwargs) -> None:
        self.client = AkamaiEdnsClient(**akamai_client_kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _extract_recordset(self, recordset, zone):
        self.logger.debug(
            "Extracting recordset %s/%s for zone %s",
            recordset.get("name"),
            recordset.get("type"),
            zone,
        )
        recordset["key"] = f'{recordset["name"]}/{recordset["type"]}'
        recordset["zone"] = zone
        for record in recordset["rdata"]:
            address_format = addresses.get_format(record)
            node_type = address_format.node_type
            if node_type:
                node_type_list = recordset.get(node_type, [])
                node_type_list.append(record)
                recordset[node_type] = node_type_list
        return recordset

    def _extract_zone(self, zone):
        try:
            record_sets = self.client.list_recordsets(zone["zone"])
        except Exception as e:
            self.logger.exception(
                "Failed to list record sets for zone: %s",
                zone["zone"],
            )
            raise e

        zone["recordsets"] = [
            self._extract_recordset(rs, zone["zone"])
            for rs in record_sets
            if rs["type"] in SUPPORTED_RECORD_TYPES
        ]
        return zone

    async def extract_records(self):
        try:
            zones = self.client.list_zones()
        except Exception as e:
            self.logger.exception("problem fetching zones: %s", e)
            raise e

        for zone in zones:
            yield self._extract_zone(zone)
