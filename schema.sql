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

-- list_size is how many entries SteamSpy's list had (full pages times 1,000
-- plus the last page). Games move between pages during a run, so some are
-- seen twice and others missed: distinct games / list_size is the coverage.
-- ALTER, so databases created before this column can reapply this file
ALTER TABLE catalog_runs ADD COLUMN IF NOT EXISTS list_size INTEGER;

-- the configured user is loaded into friends too, so marts can show "me"
-- next to friends; is_self tells them apart
ALTER TABLE friends ADD COLUMN IF NOT EXISTS is_self BOOLEAN NOT NULL DEFAULT false;

-- every game in each player's library (the user's and their friends'), from
-- GetOwnedGames. Playtimes are minutes. rtime_last_played is Steam's unix
-- timestamp, but Steam only fills it in for the API key owner's own account:
-- it's 0 for every friend's game, played or not. So 0 means unknown, and
-- "never played" has to come from playtime_forever = 0
CREATE TABLE IF NOT EXISTS player_owned_games (
    steamid            TEXT,
    appid              INTEGER,
    name               TEXT,
    playtime_forever   INTEGER,
    rtime_last_played  BIGINT,
    loaded_at          TIMESTAMP DEFAULT now(),
    PRIMARY KEY (steamid, appid)
);

-- games each player played in the last two weeks, from GetRecentlyPlayedGames
CREATE TABLE IF NOT EXISTS player_recent_games (
    steamid           TEXT,
    appid             INTEGER,
    name              TEXT,
    playtime_2weeks   INTEGER,
    playtime_forever  INTEGER,
    loaded_at         TIMESTAMP DEFAULT now(),
    PRIMARY KEY (steamid, appid)
);

-- whether Steam returned each player's library and recent games. A private
-- profile returns an empty response, which must not read as "owns nothing"
CREATE TABLE IF NOT EXISTS player_library_status (
    steamid              TEXT PRIMARY KEY,
    owned_visible        BOOLEAN,
    owned_game_count     INTEGER,
    recent_visible       BOOLEAN,
    recent_game_count    INTEGER,
    loaded_at            TIMESTAMP DEFAULT now()
);
