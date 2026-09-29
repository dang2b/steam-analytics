import logging
import time

from http_client import get_json, get_session

STEAMSPY_BASE_URL = "https://steamspy.com/api.php"

# SteamSpy allows one `all` request per minute (other requests, one per second)
CATALOG_PAGE_INTERVAL = 60
CATALOG_PAGE_SIZE = 1000

logger = logging.getLogger(__name__)


def _to_int(value):
    return int(value) if value not in (None, "") else None


def get_top100_2weeks():
    raw_games = get_json(STEAMSPY_BASE_URL, params={"request": "top100in2weeks"})
    logger.info("fetched %d games from steamspy top100in2weeks", len(raw_games))
    return raw_games


def get_catalog_pages(start_page=0, interval=CATALOG_PAGE_INTERVAL,
                      clock=time.monotonic, sleep=time.sleep):
    """Yield (page, raw_games) for each page of the full catalogue, 1,000 games a page.

    A generator, so the caller can load each page before the next is fetched.
    The wait is measured from the previous request, so time the caller spends
    loading a page counts towards it. clock and sleep are parameters so tests
    don't have to wait a real minute.
    """
    # the shared session retries 5xx after 0s, 2s and 4s, which would break
    # the one-a-minute limit; a failed page raises instead
    session = get_session(retries=0)
    page = start_page
    last_request = None
    while True:
        if last_request is not None:
            wait = interval - (clock() - last_request)
            if wait > 0:
                sleep(wait)
        last_request = clock()

        raw_games = get_json(
            STEAMSPY_BASE_URL, params={"request": "all", "page": page}, session=session
        )
        logger.info("fetched catalogue page %d: %d games", page, len(raw_games))
        if raw_games:
            yield page, raw_games

        # the page after the last one returns HTTP 500 with an empty body,
        # which looks the same as a real server error, so stop at the last
        # page (the first short one) instead of requesting past it
        if len(raw_games) < CATALOG_PAGE_SIZE:
            logger.info("catalogue ends at page %d", page)
            return
        page += 1


def parse_games(raw_games):
    games = []
    for game in raw_games.values():
        games.append((
            game["appid"],
            game["name"],
            game["developer"],
            game["publisher"],
            game["positive"],
            game["negative"],
            game["owners"],
            game["average_forever"],
            game["average_2weeks"],
            game["median_forever"],
            game["median_2weeks"],
            _to_int(game.get("price")),
            _to_int(game.get("initialprice")),
            _to_int(game.get("discount")),
            game["ccu"],
        ))
    return games
