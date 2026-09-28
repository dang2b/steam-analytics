import logging

from http_client import get_json

STEAMSPY_BASE_URL = "https://steamspy.com/api.php"

logger = logging.getLogger(__name__)


def _to_int(value):
    return int(value) if value not in (None, "") else None


def get_top100_2weeks():
    raw_games = get_json(STEAMSPY_BASE_URL, params={"request": "top100in2weeks"})
    logger.info("fetched %d games from steamspy top100in2weeks", len(raw_games))
    return raw_games


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
