-- Each player's game has at most one version per snapshot run and exactly
-- one current version, and total playtime never goes down between versions
-- (Steam only adds to it). A drop would mean rows from different players or
-- games got mixed up in the snapshot key.
with versions as (

    select
        *,
        lag(playtime_forever_minutes) over (
            partition by steam_id, appid order by observed_at
        ) as previous_minutes
    from {{ ref('stg_steam__player_playtime_history') }}

)

select steam_id, appid, 'duplicate version' as problem
from versions
group by steam_id, appid, observed_at
having count(*) > 1

union all

select steam_id, appid, 'not exactly one current version'
from versions
group by steam_id, appid
having count(*) filter (where is_latest_version) <> 1

union all

select steam_id, appid, 'playtime went down'
from versions
where playtime_forever_minutes < previous_minutes
