import requests

STEAMSPY_BASE_URL = "https://steamspy.com/api.php"


def _to_int(value):
    return int(value) if value not in (None, "") else None


def get_top100_2weeks():
    r = requests.get(STEAMSPY_BASE_URL, params={"request": "top100in2weeks"})
    r.raise_for_status()
    return r.json()


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
