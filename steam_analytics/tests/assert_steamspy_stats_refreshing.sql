{{ config(severity='warn') }}

-- Warns when most of today's top 100 has had the same SteamSpy stats for
-- more than a few days, meaning SteamSpy isn't refreshing its data and the
-- trend chart and rankings are running on old numbers.
select
    count(*) filter (where days_unchanged > {{ var('max_days_unchanged', 3) }}) as stale_games,
    count(*) as games
from {{ ref('game_freshness') }}
where is_in_latest_snapshot
having count(*) filter (where days_unchanged > {{ var('max_days_unchanged', 3) }})
    > {{ var('max_stale_share', 0.5) }} * count(*)
