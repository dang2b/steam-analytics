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

-- full SteamSpy catalogue from the paginated `all` endpoint, same columns
-- as games. Kept separate because staging flags top 100 dropouts by
-- comparing loaded_at within games, which catalogue rows would break
CREATE TABLE IF NOT EXISTS games_catalog (
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


-- one row per catalogue load, so an interrupted load resumes where it
-- stopped. Rows loaded since started_at of the latest finished run are the
-- current catalogue
CREATE TABLE IF NOT EXISTS catalog_runs (
    run_id        SERIAL PRIMARY KEY,
    started_at    TIMESTAMP NOT NULL DEFAULT now(),
    finished_at   TIMESTAMP,
    last_page     INTEGER,
    games_loaded  INTEGER NOT NULL DEFAULT 0
);
