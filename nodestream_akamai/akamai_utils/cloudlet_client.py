import logging
import re
from typing import List
from urllib.parse import urlparse

from .client import AkamaiApiClient

logger = logging.getLogger(__name__)


class AkamaiCloudletClient(AkamaiApiClient):
    def list_v2_policies(self) -> List[dict]:
        list_v2_policies_path = "/cloudlets/api/v2/policies"
        offset = 0
        policies = []
        page_size = 1000
        continue_query = True
        while continue_query:
            query_params = {"offset": offset}
            paged_response = self._get_api_from_relative_path(
                list_v2_policies_path, params=query_params
            )
            policies = policies + paged_response
            offset += page_size
            continue_query = len(paged_response) == page_size

        return policies

    def list_v3_policies(self) -> List[dict]:
        list_v3_policies_path = "/cloudlets/v3/policies"
        page_size = 9999
        query_params = {"size": page_size}
        response = self._get_api_from_relative_path(
            list_v3_policies_path, params=query_params
        )

        return response["content"]
