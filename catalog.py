"""Load the full SteamSpy catalogue into games_catalog, one page at a time.

Takes over an hour: SteamSpy allows one catalogue page a minute. Runs
separately from main.py so the daily top 100 load stays fast.
"""
import logging
import sys
import time

import extract_steamspy
import load

logger = logging.getLogger("catalog")


def run(start_page=0):
    total = 0
    for page, raw_games in extract_steamspy.get_catalog_pages(start_page=start_page):
        games = extract_steamspy.parse_games(raw_games)
        load.load_catalog_page(games)
        total += len(games)
        logger.info("page %d loaded, %d games so far", page, total)
    return total


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    start = time.monotonic()
    logger.info("catalogue load started")
    try:
        total = run()
    except Exception:
        logger.exception("catalogue load failed after %.1fs", time.monotonic() - start)
        sys.exit(1)
    logger.info("catalogue load finished: %d games in %.1fs", total, time.monotonic() - start)
