-- The full catalogue is tens of thousands of games. A finished run with far
-- fewer means pagination stopped early, e.g. because SteamSpy made pages
-- smaller than the 1,000 games catalog.py treats as a full page. CI loads a
-- handful of fixture games, so it lowers min_catalog_games.
select run_id, games_loaded
from {{ source('raw', 'catalog_runs') }}
where run_id = (
    select max(run_id)
    from {{ source('raw', 'catalog_runs') }}
    where finished_at is not null
)
and games_loaded < {{ var('min_catalog_games', 10000) }}
