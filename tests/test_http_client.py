from http_client import get_session


def test_session_retries_rate_limits_and_server_errors():
    retry = get_session().get_adapter("https://steamspy.com").max_retries

    assert retry.total == 3
    assert {429, 500, 502, 503, 504} <= set(retry.status_forcelist)
    assert retry.respect_retry_after_header
