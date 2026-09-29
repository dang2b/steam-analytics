import pytest
import requests

from http_client import get_json, get_session


def test_session_retries_rate_limits_and_server_errors():
    retry = get_session().get_adapter("https://steamspy.com").max_retries

    assert retry.total == 3
    assert {429, 500, 502, 503, 504} <= set(retry.status_forcelist)
    assert retry.respect_retry_after_header


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error

    def get(self, url, params=None, timeout=None):
        if self.error:
            raise self.error
        return self.response


def test_http_error_hides_api_key():
    response = requests.Response()
    response.status_code = 403
    response.reason = "Forbidden"
    response.url = "https://api.steampowered.com/x?key=SECRET&steamid=1"

    with pytest.raises(requests.HTTPError) as exc:
        get_json("https://api.steampowered.com/x", session=FakeSession(response=response))

    assert "SECRET" not in str(exc.value)
    assert "key=REDACTED&steamid=1" in str(exc.value)
    assert exc.value.__suppress_context__


def test_connection_error_hides_api_key():
    error = requests.ConnectionError("Max retries exceeded with url: /x?key=SECRET")

    with pytest.raises(requests.ConnectionError) as exc:
        get_json("https://api.steampowered.com/x", session=FakeSession(error=error))

    assert "SECRET" not in str(exc.value)
