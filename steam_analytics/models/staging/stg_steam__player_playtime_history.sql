with snapshot as (

    select * from {{ ref('player_games_snapshot') }}

),

renamed as (

    select
        steamid as steam_id,
        appid,
        name as game_name,
        playtime_forever as playtime_forever_minutes,

        -- the check strategy stamps each version with the snapshot run's
        -- time, which runs right after the daily load
        dbt_valid_from as observed_at,
        dbt_valid_from::date as observed_date,
        dbt_valid_to is null as is_latest_version

    from snapshot

)

select * from renamed
