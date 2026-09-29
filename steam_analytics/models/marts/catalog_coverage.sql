-- SteamSpy orders the catalogue by an owners estimate that shifts during the
-- day, so over a run of an hour or more some games move between pages: a
-- game moving to a later page is seen twice, one moving to an earlier page
-- is missed. This measures both for the latest finished run.

with latest_run as (

    select * from {{ ref('stg_steamspy__catalog_runs') }}
    where is_finished
    order by started_at desc
    limit 1

),

latest_catalog as (

    select count(*) as distinct_games
    from {{ ref('stg_steamspy__catalog') }}
    where is_in_latest_catalog

)

select
    latest_run.run_id,
    latest_run.started_at,
    latest_run.finished_at,
    latest_run.run_hours,
    latest_run.pages_loaded,
    latest_run.list_size,
    latest_run.games_upserted,
    latest_catalog.distinct_games,
    latest_run.games_upserted - latest_catalog.distinct_games as duplicate_rows,
    -- each duplicate took the place of a game that was never seen
    latest_run.list_size - latest_catalog.distinct_games as games_missed_estimate,
    round(latest_catalog.distinct_games::numeric / nullif(latest_run.list_size, 0), 4)
        as coverage
from latest_run
cross join latest_catalog
