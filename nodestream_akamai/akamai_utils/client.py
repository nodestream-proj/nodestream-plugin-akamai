import functools
import logging
import time
from urllib.parse import urljoin

from akamai.edgegrid import EdgeGridAuth
from requests import HTTPError, Session
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
        response = None
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
                logger.warning(
                    "Received 500 response for 'GET %s'. Retrying...", full_url
                )
                response = self.session.get(full_url, params=params, headers=headers)

            # Back off for rate limit 429
            if response.status_code == 429:
                # Increase bacoff for next attempt
                next_backoff_index = backoff_index + 1
                if next_backoff_index > len(backoff_delays):
                    logger.warning(
                        "Received 429 response for 'GET %s' and backoff limit exceeded.",
                        full_url,
                    )
                else:
                    backoff = backoff_delays[backoff_index]
                    logger.warning(
                        "Received 429 response for 'GET %s'. Waiting for %s seconds before retrying",
                        full_url,
                        backoff,
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
        if response:
            response.raise_for_status()
            # raise for status only handles: 400 <= status_code < 600
            msg = f"Unexpected status {response.status_code} for url: {response.url}"
            raise HTTPError(msg, response=response)
        msg = "Missing response object in _get_api_from_relative_path"
        raise SystemError(msg)

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

        response = None
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
        if response:
            response.raise_for_status()
            # raise for status only handles: 400 <= status_code < 600
            msg = f"Unexpected status {response.status_code} for url: {response.url}"
            raise HTTPError(msg, response=response)
        msg = "Missing response object in _post_api_from_relative_path"
        raise SystemError(msg)

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
