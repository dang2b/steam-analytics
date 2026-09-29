import pytest
import requests

import extract_steamspy
from extract_steamspy import CATALOG_PAGE_SIZE, get_catalog_pages, parse_games

# column order load.load_games inserts in
APPID, OWNERS, PRICE, INITIAL_PRICE, DISCOUNT, CCU = 0, 6, 11, 12, 13, 14


def games_by_appid(raw):
    return {game[APPID]: game for game in parse_games(raw)}


def test_one_row_per_game(steamspy_sample):
    games = parse_games(steamspy_sample)

    assert len(games) == len(steamspy_sample)
    assert all(len(game) == 15 for game in games)


def test_prices_become_integer_cents(steamspy_sample):
    rust = games_by_appid(steamspy_sample)[252490]

    assert rust[PRICE] == 1999
    assert rust[INITIAL_PRICE] == 3999
    assert rust[DISCOUNT] == 50


def test_free_game_price_is_zero_not_null(steamspy_sample):
    cs = games_by_appid(steamspy_sample)[730]

    assert cs[PRICE] == 0


def test_missing_or_empty_price_becomes_null(steamspy_sample):
    game = dict(steamspy_sample["730"], price="", initialprice=None)
    del game["discount"]

    [parsed] = parse_games({"730": game})

    assert parsed[PRICE] is None
    assert parsed[INITIAL_PRICE] is None
    assert parsed[DISCOUNT] is None


def test_owners_bucket_kept_as_raw_text(steamspy_sample):
    # parsing the bucket into numbers is dbt staging's job
    cs = games_by_appid(steamspy_sample)[730]

    assert cs[OWNERS] == "100,000,000 .. 200,000,000"


class FakeClock:
    """Time only moves when sleep is called, or when a test advances it."""

    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


def fake_page(page, size):
    return {f"{page}-{i}": {"appid": i} for i in range(size)}


@pytest.fixture
def fake_catalog(monkeypatch):
    """Pages 0 and 1 are full, page 2 is the short last page, and anything
    after it fails like the live API. Records requested pages."""
    requested = []

    def fake_get_json(url, params=None, session=None):
        page = params["page"]
        requested.append(page)
        if page > 2:
            raise requests.HTTPError("500 Server Error")
        return fake_page(page, 5 if page == 2 else CATALOG_PAGE_SIZE)

    monkeypatch.setattr(extract_steamspy, "get_json", fake_get_json)
    return requested


def pages(clock, **kwargs):
    return get_catalog_pages(clock=clock.time, sleep=clock.sleep, **kwargs)


def test_catalog_stops_at_short_page_without_requesting_past_it(clock, fake_catalog):
    fetched = [(page, len(games)) for page, games in pages(clock)]

    assert fetched == [(0, CATALOG_PAGE_SIZE), (1, CATALOG_PAGE_SIZE), (2, 5)]
    assert fake_catalog == [0, 1, 2]


def test_catalog_error_raises_instead_of_ending_early(clock, monkeypatch):
    # a 500 mid-catalogue must not look like the end of the catalogue
    def failing_get_json(url, params=None, session=None):
        if params["page"] == 1:
            raise requests.HTTPError("500 Server Error")
        return fake_page(params["page"], CATALOG_PAGE_SIZE)

    monkeypatch.setattr(extract_steamspy, "get_json", failing_get_json)

    with pytest.raises(requests.HTTPError):
        list(pages(clock))


def test_catalog_does_not_retry_quickly(clock, monkeypatch):
    sessions = []

    def fake_get_json(url, params=None, session=None):
        sessions.append(session)
        return {}

    monkeypatch.setattr(extract_steamspy, "get_json", fake_get_json)
    list(pages(clock))

    assert sessions[0].get_adapter("https://steamspy.com").max_retries.total == 0


def test_catalog_waits_full_interval_between_requests(clock, fake_catalog):
    list(pages(clock, interval=60))

    # no wait before the first request, then one before each of the other two
    assert clock.sleeps == [60, 60]


def test_catalog_counts_callers_time_towards_the_wait(clock, fake_catalog):
    for _ in pages(clock, interval=60):
        clock.now += 20  # e.g. loading the page into Postgres

    assert clock.sleeps == [40, 40]


def test_catalog_skips_wait_when_caller_is_slower_than_interval(clock, fake_catalog):
    for _ in pages(clock, interval=60):
        clock.now += 90

    assert clock.sleeps == []


def test_catalog_can_wait_before_first_request(clock, fake_catalog):
    list(pages(clock, interval=60, wait_first=True))

    assert clock.sleeps == [60, 60, 60]


def test_catalog_resumes_from_start_page(clock, fake_catalog):
    fetched = [page for page, _ in pages(clock, start_page=2)]

    assert fetched == [2]
    assert fake_catalog == [2]


def test_catalog_pages_parse_like_top100(clock, monkeypatch, steamspy_sample):
    # the `all` endpoint returns the same fields as top100in2weeks
    # the sample has fewer than 1,000 games, so it's also the last page
    monkeypatch.setattr(
        extract_steamspy, "get_json", lambda url, params=None, session=None: steamspy_sample
    )

    [(_, raw_games)] = list(pages(clock))

    assert len(parse_games(raw_games)) == len(steamspy_sample)
