with catalog as (

    select * from {{ ref('stg_steamspy__catalog') }}
    where is_in_latest_catalog

),

top100 as (

    select appid from {{ ref('stg_steamspy__games') }}
    where is_in_latest_top100

),

games as (

    select
        catalog.owners_bucket,
        catalog.owners_min,
        catalog.owners_max,
        -- midpoint of the SteamSpy range: rough, especially for the widest buckets
        (catalog.owners_min + catalog.owners_max) / 2 as owners_estimate,
        top100.appid is not null as is_in_top100
    from catalog
    left join top100 on top100.appid = catalog.appid

),

buckets as (

    select
        owners_bucket,
        owners_min,
        owners_max,
        count(*) as game_count,
        count(*) filter (where is_in_top100) as top100_game_count,
        sum(owners_estimate) as owners_estimate,
        coalesce(sum(owners_estimate) filter (where is_in_top100), 0)
            as top100_owners_estimate
    from games
    group by owners_bucket, owners_min, owners_max

)

select
    *,
    round(game_count::numeric / sum(game_count) over (), 4) as share_of_games,
    round(owners_estimate::numeric / nullif(sum(owners_estimate) over (), 0), 4)
        as share_of_owners
from buckets
