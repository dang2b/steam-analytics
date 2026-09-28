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


def load_games(games):
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO games (
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
            """,
            games,
        )
    logger.info("upserted %d rows into games", len(games))
