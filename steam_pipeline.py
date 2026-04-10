import requests
import os
from dotenv import load_dotenv

def get_friend_ids(steam_id):
    payload = {'key': STEAM_API_KEY, 'steamid': '76561198314131071'}
    r = requests.get('https://api.steampowered.com/ISteamUser/GetFriendList/v1/', params=payload)

    friend_ids = []
    for friend in r.json()["friendslist"]["friends"]:
        friend_ids.append(friend["steamid"])
    return friend_ids

def get_friend_summaries(friend_ids):
    r = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/', params={'key': STEAM_API_KEY, 'steamids': ','.join(friend_ids)})

    for player in r.json()["response"]["players"]:
        print(player["personaname"])

if __name__ == "__main__":
    load_dotenv()
    STEAM_USER_ID = os.getenv('STEAM_USER_ID')
    STEAM_API_KEY = os.getenv('STEAM_API_KEY')

    get_friend_summaries(get_friend_ids(STEAM_USER_ID))