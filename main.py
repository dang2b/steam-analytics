import logging
import sys
import time

import extract_friends
import extract_steamspy
import load

logger = logging.getLogger("pipeline")


def run():
    # games first: they feed the marts and the history snapshot, so a
    # friends API problem (private list, expired key) shouldn't block them
    raw_games = extract_steamspy.get_top100_2weeks()
    games = extract_steamspy.parse_games(raw_games)
    load.load_games(games)

    ids = extract_friends.get_friend_ids()
    players = extract_friends.get_friend_summaries(ids)
    load.load_friends(players)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    start = time.monotonic()
    logger.info("pipeline started")
    try:
        run()
    except Exception:
        logger.exception("pipeline failed after %.1fs", time.monotonic() - start)
        sys.exit(1)
    logger.info("pipeline finished in %.1fs", time.monotonic() - start)
