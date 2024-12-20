import functools
import logging
from urllib.parse import urljoin

import requests
from akamai.edgegrid import EdgeGridAuth
from requests import Session
from requests.adapters import HTTPAdapter
from tenacity import (
    Retrying,
    after_log,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.util.retry import Retry

PROTOCOL_HTTP = "http://"
PROTOCOL_HTTPS = "https://"
CREDENTIAL_TIMEOUT_SECONDS = 300


class AkamaiClientException(IOError):
    def __init__(self, msg, text):
        super(AkamaiClientException, self).__init__(msg)
        self.text = text


class AkamaiApiClient:
    def __init__(
        self,
        base_url,
        client_token,
        client_secret,
        access_token,
        account_key=None,
        max_retries=5,
        retry_wait_seconds_min=5,
        retry_wait_seconds_max=180,
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
        self.max_retries = max_retries
        self.retry_wait_seconds_min = retry_wait_seconds_min
        self.retry_wait_seconds_max = retry_wait_seconds_max
        self.logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")

    @property
    def _retryer(self):
        return Retrying(
            retry=retry_if_exception_type(
                (requests.exceptions.HTTPError, AkamaiClientException)
            ),
            wait=wait_exponential(
                min=self.retry_wait_seconds_min, max=self.retry_wait_seconds_max
            ),
            stop=stop_after_attempt(self.max_retries),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
            after=after_log(self.logger, logging.ERROR),
            reraise=True,
        )

    def _get_api_from_relative_path(
        self,
        path,
        params=None,
        headers=None,
    ):
        response = self._retryer(
            self._retrying_get_api_from_relative_path,
            path,
            params,
            headers,
        )
        return response.json()

    def _retrying_get_api_from_relative_path(
        self, path, params=None, headers=None
    ) -> requests.Response:
        full_url = urljoin(self.base_url, path)

        # Insert account switch key
        if self.account_key is not None:
            if params is None:
                params = {}
            params["accountSwitchKey"] = self.account_key
        self.logger.debug(
            "_get_api_from_relative_path(path=%s, params=%s, headers=%s)",
            path,
            params,
            headers,
        )
        response = self.session.get(full_url, params=params, headers=headers)
        response.raise_for_status()
        # Return body if 200
        if response.status_code == requests.codes.ok:
            return response

        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise AkamaiClientException(
            f"response.status_code: {response.status_code}", response.text
        )

    def _post_api_from_relative_path(self, path, body, params=None, headers=None):
        response = self._retryer(
            self._retrying_post_api_from_relative_path,
            path,
            body,
            params,
            headers,
        )
        return response.json()

    def _retrying_post_api_from_relative_path(
        self,
        path,
        body,
        params=None,
        headers=None,
    ):
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
        response = self.session.post(
            full_url, params=params, headers=request_headers, json=body
        )

        response.raise_for_status()
        # raise for status only handles: 400 <= status_code < 600
        raise AkamaiClientException(
            f"response.status_code: {response.status_code}", response.text
        )

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
