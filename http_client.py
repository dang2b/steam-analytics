import logging
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 10
RETRY_STATUSES = (429, 500, 502, 503, 504)

# the Steam Web API takes its key as a query parameter, and both requests'
# error messages and urllib3's retry warnings include the full URL
_API_KEY_PARAM = re.compile(r"(key=)[^&\s'\"]+")


def redact(text):
    return _API_KEY_PARAM.sub(r"\1REDACTED", text)


class _RedactFilter(logging.Filter):
    def filter(self, record):
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


logging.getLogger("urllib3.connectionpool").addFilter(_RedactFilter())


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
    try:
        r = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        # `from None` drops the original exception, which would otherwise
        # print the unredacted URL in the traceback
        raise type(e)(redact(str(e)), response=e.response, request=e.request) from None
    return r.json()
