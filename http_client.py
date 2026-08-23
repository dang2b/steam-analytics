import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 10
RETRY_STATUSES = (429, 500, 502, 503, 504)


def get_session(retries=3, backoff_factor=1.0):
    # backoff_factor=1.0 waits 0s, 2s, 4s between attempts
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_json(url, params=None, session=None):
    session = session or get_session()
    r = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()
