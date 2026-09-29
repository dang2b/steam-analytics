-- The full catalogue is tens of thousands of games. A finished run with far
-- fewer means pagination stopped early, e.g. because SteamSpy made pages
-- smaller than the 1,000 games catalog.py treats as a full page. CI loads a
-- handful of fixture games, so it lowers min_catalog_games.
select run_id, list_size, games_upserted
from {{ ref('stg_steamspy__catalog_runs') }}
where run_id = (
    select max(run_id)
    from {{ ref('stg_steamspy__catalog_runs') }}
    where is_finished
)
-- list_size is null for runs finished before it was recorded
and coalesce(list_size, games_upserted) < {{ var('min_catalog_games', 10000) }}
