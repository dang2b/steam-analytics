import extract_friends
import extract_steamspy
import load


if __name__ == "__main__":
    ids = extract_friends.get_friend_ids()
    players = extract_friends.get_friend_summaries(ids)
    load.load_friends(players)

    raw_games = extract_steamspy.get_top100_2weeks()
    games = extract_steamspy.parse_games(raw_games)
    load.load_games(games)