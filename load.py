import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def load_friends(players):
    with psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    ) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO friends (steamid, 
personaname, profileurl, personastate)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (steamid) DO UPDATE SET
                    personaname  = EXCLUDED.personaname,
                    personastate = EXCLUDED.personastate;
                """,
                players,
            )
