import functools
import logging
import time
from urllib.parse import urljoin

from akamai.edgegrid import EdgeGridAuth
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

PROTOCOL_HTTP = "http://"
PROTOCOL_HTTPS = "https://"
CREDENTIAL_TIMEOUT_SECONDS = 300


class AkamaiApiClient:
    def __init__(
        self, base_url, client_token, client_secret, access_token, account_key=None
    ):
        self.base_url = base_url
        self.error_count = 0
        self.page_size = 100
        self.session = self._resilient_session_factory()
        self.session.auth = EdgeGridAuth(
            client_token=client_token,
            client_secret=client_secret,
            access_token=access_token,
            max_body=128 * 1024,  # TODO: Completely Arbitrary Currently
        )
        self.account_key = account_key

    def _get_api_from_relative_path(
        self, path, params=None, headers=None, backoff_index=None
    ):
        full_url = urljoin(self.base_url, path)

        backoff_delays = [5, 10, 20, 60, 180]
        if backoff_index is None:
            backoff_index = 0

        # Insert account switch key
        if self.account_key is not None:
            if params is None:
                params = {}
            params["accountSwitchKey"] = self.account_key

        for sleepy_seconds in range(5):
            if sleepy_seconds:
                time.sleep(sleepy_seconds)
            response = self.session.get(full_url, params=params, headers=headers)
            # Retry once for temporary 500 errors
            if response.status_code == 500:
                logger.error(f"Received 500 response for 'GET {full_url}'. Retrying...")
                response = self.session.get(full_url, params=params, headers=headers)

            # Back off for rate limit 429
            if response.status_code == 429:
                # Increase bacoff for next attempt
                next_backoff_index = backoff_index + 1
                if next_backoff_index > len(backoff_delays):
                    logger.error(
                        f"Received 429 response for 'GET {full_url}' and backoff limit exceeded."
                    )
                else:
                    backoff = backoff_delays[backoff_index]
                    logger.error(
                        f"Received 429 response for 'GET {full_url}'. Waiting for {backoff} seconds before retrying"
                    )
                    time.sleep(backoff)
                    response = self._get_api_from_relative_path(
                        path,
                        params=params,
                        headers=headers,
                        backoff_index=next_backoff_index,
                    )

            # Return body if 200
            if response.status_code == 200:
                return response.json()
            self.error_count += 1
            logger.error(
                "response.status_code: %s, response.text: %s",
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise Exception(f"response.status_code: {response.status_code}", response.text)

    def _post_api_from_relative_path(self, path, body, params=None, headers=None):
        full_url = urljoin(self.base_url, path)

        # Insert account switch key
        if self.account_key is not None:
            if params is None:
                params = {}
            params["accountSwitchKey"] = self.account_key

        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if isinstance(headers, dict):
            for header in headers:
                request_headers[header] = headers[header]

        for sleepy_seconds in range(5):
            if sleepy_seconds:
                time.sleep(sleepy_seconds)
            response = self.session.post(
                full_url, params=params, headers=request_headers, json=body
            )
            if response.status_code == 200:
                return response.json()
            self.error_count += 1
            logger.error(
                "response.status_code: %s, response.text: %s",
                response.status_code,
                response.text,
            )
        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise Exception(f"response.status_code: {response.status_code}", response.text)

    def keep_first(self, iterable, key=None):
        if key is None:
            key = lambda x: x

        seen = set()
        for elem in iterable:
            k = key(elem)
            if k in seen:
                continue

            yield elem
            seen.add(k)

    @staticmethod
    def _resilient_session_factory(timeout=300, retry_count=5) -> Session:
        session = Session()
        retries = Retry(
            total=retry_count, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
        )
        session.mount(PROTOCOL_HTTP, HTTPAdapter(max_retries=retries))
        session.mount(PROTOCOL_HTTPS, HTTPAdapter(max_retries=retries))
        session.request = functools.partial(session.request, timeout=timeout)  # Seconds
        session.send = functools.partial(session.send, timeout=timeout)  # Seconds
        return session
