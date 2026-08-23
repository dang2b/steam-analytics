CREATE TABLE IF NOT EXISTS friends (
    steamid      TEXT PRIMARY KEY,
    personaname  TEXT,
    profileurl   TEXT,
    personastate INTEGER,
    loaded_at    TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS games (
    appid                     INTEGER PRIMARY KEY,
    name                      TEXT,
    developer                 TEXT,
    publisher                 TEXT,
    positive_reviews          INTEGER,
    negative_reviews          INTEGER,
    owners                    TEXT,
    average_playtime_forever  INTEGER,
    average_playtime_2weeks   INTEGER,
    median_playtime_forever   INTEGER,
    median_playtime_2weeks    INTEGER,
    price_cents               INTEGER,
    initial_price_cents       INTEGER,
    discount_pct              INTEGER,
    concurrent_users          INTEGER,
    loaded_at                 TIMESTAMP DEFAULT now()
);