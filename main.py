import extract
import load



if __name__ == "__main__":
    ids = extract.get_friend_ids()
    players = extract.get_friend_summaries(ids)
    load.load_friends(players)