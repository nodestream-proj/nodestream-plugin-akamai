import functools
import socket
import time

from requests import Session
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests.models import PreparedRequest
from urllib3.util.retry import Retry

PROTOCOL_HTTP = "http://"
PROTOCOL_HTTPS = "https://"
CREDENTIAL_TIMEOUT_SECONDS = 300


def resilient_session_factory(timeout=300, retry_count=5) -> Session:
    session = Session()
    retries = Retry(
        total=retry_count, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
    )
    session.mount(PROTOCOL_HTTP, HTTPAdapter(max_retries=retries))
    session.mount(PROTOCOL_HTTPS, HTTPAdapter(max_retries=retries))
    session.request = functools.partial(session.request, timeout=timeout)  # Seconds
    session.send = functools.partial(session.send, timeout=timeout)  # Seconds
    return session
