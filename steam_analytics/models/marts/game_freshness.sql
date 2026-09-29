-- How long each game's SteamSpy stats have gone unchanged. The snapshot
-- records every load, but SteamSpy doesn't refresh its numbers every day,
-- so identical values can repeat for days. A streak is a run of consecutive
-- snapshots with the same concurrent users and review count.

with daily as (

    select * from {{ ref('game_daily_stats') }}

),

flagged as (

    select
        *,
        -- 1 when the stats differ from the game's previous snapshot; the
        -- first snapshot counts as a change, so it starts the first streak.
        -- Price is left out: it changes independently of the stats
        case
            when lag(concurrent_users) over w is distinct from concurrent_users
              or lag(total_reviews) over w is distinct from total_reviews
            then 1 else 0
        end as is_change
    from daily
    window w as (partition by appid order by snapshot_date)

),

streaks as (

    select
        *,
        -- a running count of changes numbers the streaks; comparing values
        -- this way, instead of grouping by value, keeps A, B, A as three
        -- separate streaks
        sum(is_change) over (partition by appid order by snapshot_date) as streak_id
    from flagged

),

current_streak as (

    select *
    from (
        select *, max(streak_id) over (partition by appid) as latest_streak_id
        from streaks
    ) numbered
    where streak_id = latest_streak_id

)

select
    appid,
    max(game_name) as game_name,
    min(snapshot_date) as unchanged_since,
    max(snapshot_date) as last_snapshot_date,
    max(snapshot_date) = (select max(snapshot_date) from daily) as is_in_latest_snapshot,
    count(*) as snapshots_unchanged,
    max(snapshot_date) - min(snapshot_date) + 1 as days_unchanged
from current_streak
group by appid
