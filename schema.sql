CREATE TABLE IF NOT EXISTS friends (
    steamid      TEXT PRIMARY KEY, 
    personaname  TEXT,
    profileurl   TEXT,
    personastate INTEGER,
    loaded_at    TIMESTAMP DEFAULT now()
);