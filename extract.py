import requests
from config import STEAM_API_KEY, STEAM_USER_ID


def get_friend_ids(steam_user_id=STEAM_USER_ID):
    payload = {'key': STEAM_API_KEY, 'steamid': steam_user_id}
    r = requests.get('https://api.steampowered.com/ISteamUser/GetFriendList/v1/', params=payload)
    print(r.status_code, r.text)
    print(payload)

    friend_ids = []
    for friend in r.json()["friendslist"]["friends"]:
        friend_ids.append(friend["steamid"])
    return friend_ids

def get_friend_summaries(friend_ids):
    r = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/', params={'key': STEAM_API_KEY, 'steamids': ','.join(friend_ids)})

    players = []
    for player in r.json()["response"]["players"]:
        players.append((
            player["steamid"],
            player["personaname"], 
            player["profileurl"],
            player["personastate"],
        ))
    return players