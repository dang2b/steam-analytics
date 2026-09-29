import logging
from contextlib import contextmanager

import psycopg2

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

logger = logging.getLogger(__name__)


@contextmanager
def connect():
    # psycopg2's own `with conn:` only commits or rolls back the transaction;
    # it leaves the connection open, so close it explicitly
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def load_friends(players):
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO friends (steamid, personaname, profileurl, personastate)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (steamid) DO UPDATE SET
                personaname  = EXCLUDED.personaname,
                personastate = EXCLUDED.personastate,
                loaded_at    = now();
            """,
            players,
        )
    logger.info("upserted %d rows into friends", len(players))


# games and games_catalog share columns, so they share one upsert. The table
# name is formatted in, which is safe only because it comes from this dict,
# never from input
_UPSERT_GAMES = """
    INSERT INTO {table} (
        appid, name, developer, publisher,
        positive_reviews, negative_reviews, owners,
        average_playtime_forever, average_playtime_2weeks,
        median_playtime_forever, median_playtime_2weeks,
        price_cents, initial_price_cents, discount_pct,
        concurrent_users
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (appid) DO UPDATE SET
        name                     = EXCLUDED.name,
        developer                = EXCLUDED.developer,
        publisher                = EXCLUDED.publisher,
        positive_reviews         = EXCLUDED.positive_reviews,
        negative_reviews         = EXCLUDED.negative_reviews,
        owners                   = EXCLUDED.owners,
        average_playtime_forever = EXCLUDED.average_playtime_forever,
        average_playtime_2weeks  = EXCLUDED.average_playtime_2weeks,
        median_playtime_forever  = EXCLUDED.median_playtime_forever,
        median_playtime_2weeks   = EXCLUDED.median_playtime_2weeks,
        price_cents              = EXCLUDED.price_cents,
        initial_price_cents      = EXCLUDED.initial_price_cents,
        discount_pct             = EXCLUDED.discount_pct,
        concurrent_users         = EXCLUDED.concurrent_users,
        loaded_at                = now();
"""
UPSERT_SQL = {table: _UPSERT_GAMES.format(table=table) for table in ("games", "games_catalog")}


def load_games(games):
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_SQL["games"], games)
    logger.info("upserted %d rows into games", len(games))


def start_or_resume_catalog_run():
    """Return (run_id, next_page, resumed), resuming the latest run if it didn't finish."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT run_id, last_page FROM catalog_runs
            WHERE finished_at IS NULL
            ORDER BY run_id DESC
            LIMIT 1;
            """
        )
        unfinished = cur.fetchone()
        if unfinished:
            run_id, last_page = unfinished
            return run_id, 0 if last_page is None else last_page + 1, True

        cur.execute("INSERT INTO catalog_runs DEFAULT VALUES RETURNING run_id;")
        return cur.fetchone()[0], 0, False


def load_catalog_page(run_id, page, games):
    # the page and its checkpoint commit together: a crash can't leave a
    # page saved but unrecorded, or recorded but unsaved. One short
    # transaction per page also means no connection stays open all run
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_SQL["games_catalog"], games)
        cur.execute(
            """
            UPDATE catalog_runs
            SET last_page = %s, games_loaded = games_loaded + %s
            WHERE run_id = %s;
            """,
            (page, len(games), run_id),
        )
    logger.info("upserted %d rows into games_catalog (run %d, page %d)", len(games), run_id, page)


def finish_catalog_run(run_id):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE catalog_runs SET finished_at = now() WHERE run_id = %s;", (run_id,)
        )
