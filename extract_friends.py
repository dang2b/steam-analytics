import logging

from config import STEAM_API_KEY, STEAM_USER_ID
from http_client import get_json

FRIEND_LIST_URL = 'https://api.steampowered.com/ISteamUser/GetFriendList/v1/'
PLAYER_SUMMARIES_URL = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/'
OWNED_GAMES_URL = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
RECENT_GAMES_URL = 'https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/'

logger = logging.getLogger(__name__)


def get_friend_ids(steam_user_id=STEAM_USER_ID):
    data = get_json(FRIEND_LIST_URL, params={'key': STEAM_API_KEY, 'steamid': steam_user_id})

    friend_ids = []
    for friend in data["friendslist"]["friends"]:
        friend_ids.append(friend["steamid"])
    logger.info("fetched %d friend ids", len(friend_ids))
    return friend_ids


def get_player_summaries(friend_ids, self_id=STEAM_USER_ID):
    # the user's own profile comes along, so marts can show "me" next to friends
    data = get_json(
        PLAYER_SUMMARIES_URL,
        params={'key': STEAM_API_KEY, 'steamids': ','.join([self_id, *friend_ids])},
    )
    players = parse_player_summaries(data, self_id)
    logger.info("fetched %d player summaries", len(players))
    return players


def parse_player_summaries(data, self_id=None):
    players = []
    for player in data["response"]["players"]:
        players.append((
            player["steamid"],
            player["personaname"],
            player["profileurl"],
            player["personastate"],
            player["steamid"] == self_id,
        ))
    return players


def get_owned_games(steamid):
    return get_json(OWNED_GAMES_URL, params={
        'key': STEAM_API_KEY,
        'steamid': steamid,
        'include_appinfo': 1,           # game names
        'include_played_free_games': 1,  # free games only count once played
    })["response"]


def get_recent_games(steamid):
    return get_json(
        RECENT_GAMES_URL, params={'key': STEAM_API_KEY, 'steamid': steamid}
    )["response"]


def parse_owned_games(steamid, response):
    """Return (rows, visible). A private library comes back as an empty response,
    with no game_count, which has to stay apart from a library with no games."""
    visible = "game_count" in response
    rows = [
        (
            steamid,
            game["appid"],
            game.get("name"),
            game["playtime_forever"],
            game.get("rtime_last_played", 0),
        )
        for game in response.get("games", [])
    ]
    return rows, visible


def parse_recent_games(steamid, response):
    """Return (rows, visible). Players with nothing recent get total_count 0;
    hidden playtime gets no total_count at all."""
    visible = "total_count" in response
    rows = [
        (
            steamid,
            game["appid"],
            game.get("name"),
            game["playtime_2weeks"],
            game["playtime_forever"],
        )
        for game in response.get("games", [])
    ]
    return rows, visible


def get_player_games(steamids, fetch_owned=get_owned_games, fetch_recent=get_recent_games):
    """Fetch every player's library and recent games.

    Returns (statuses, owned_rows, recent_rows), ready for load.load_player_games.
    The fetch functions are parameters so CI can feed in fixtures instead.
    """
    statuses, owned_rows, recent_rows = [], [], []
    for steamid in steamids:
        owned, owned_visible = parse_owned_games(steamid, fetch_owned(steamid))
        recent, recent_visible = parse_recent_games(steamid, fetch_recent(steamid))
        statuses.append((steamid, owned_visible, len(owned), recent_visible, len(recent)))
        owned_rows += owned
        recent_rows += recent

    hidden = sum(not status[1] for status in statuses)
    logger.info(
        "fetched %d owned and %d recent games for %d players (%d libraries hidden)",
        len(owned_rows), len(recent_rows), len(steamids), hidden,
    )
    return statuses, owned_rows, recent_rows
