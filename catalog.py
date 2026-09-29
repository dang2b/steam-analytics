"""Load the full SteamSpy catalogue into games_catalog, one page at a time.

Takes over an hour: SteamSpy allows one catalogue page a minute. Runs
separately from main.py so the daily top 100 load stays fast. Progress is
checkpointed per page in catalog_runs, so rerunning after a failure
continues from the next page instead of starting over.
"""
import logging
import sys
import time

import extract_steamspy
import load

logger = logging.getLogger("catalog")


def run():
    run_id, start_page, resumed = load.start_or_resume_catalog_run()
    if resumed:
        logger.info("resuming catalogue run %d from page %d", run_id, start_page)
    else:
        logger.info("starting catalogue run %d", run_id)

    total = 0
    # a resumed run waits first: the request that crashed the last attempt
    # still counts towards SteamSpy's one-a-minute limit
    pages = extract_steamspy.get_catalog_pages(start_page=start_page, wait_first=resumed)
    for page, raw_games in pages:
        games = extract_steamspy.parse_games(raw_games)
        load.load_catalog_page(run_id, page, games)
        total += len(games)
        logger.info("page %d loaded, %d games so far this attempt", page, total)

    load.finish_catalog_run(run_id)
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
