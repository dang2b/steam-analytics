import logging

from config import STEAM_API_KEY, STEAM_USER_ID
from http_client import get_json

FRIEND_LIST_URL = 'https://api.steampowered.com/ISteamUser/GetFriendList/v1/'
PLAYER_SUMMARIES_URL = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/'

logger = logging.getLogger(__name__)


def get_friend_ids(steam_user_id=STEAM_USER_ID):
    data = get_json(FRIEND_LIST_URL, params={'key': STEAM_API_KEY, 'steamid': steam_user_id})

    friend_ids = []
    for friend in data["friendslist"]["friends"]:
        friend_ids.append(friend["steamid"])
    logger.info("fetched %d friend ids", len(friend_ids))
    return friend_ids


def get_friend_summaries(friend_ids):
    data = get_json(
        PLAYER_SUMMARIES_URL,
        params={'key': STEAM_API_KEY, 'steamids': ','.join(friend_ids)},
    )
    players = parse_player_summaries(data)
    logger.info("fetched %d player summaries", len(players))
    return players


def parse_player_summaries(data):
    players = []
    for player in data["response"]["players"]:
        players.append((
            player["steamid"],
            player["personaname"],
            player["profileurl"],
            player["personastate"],
        ))
    return players
