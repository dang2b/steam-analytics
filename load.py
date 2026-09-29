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


def _upsert_games(table, games):
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_SQL[table], games)
    logger.info("upserted %d rows into %s", len(games), table)


def load_games(games):
    _upsert_games("games", games)


def load_catalog_page(games):
    # one short transaction per page: a page is saved even if a later one
    # fails, and no connection sits open through the hour-long run
    _upsert_games("games_catalog", games)
