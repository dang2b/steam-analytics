with snapshot as (

    select * from {{ ref('games_snapshot') }}

),

renamed as (

    select
        appid,
        name as game_name,
        concurrent_users,
        positive_reviews,
        negative_reviews,
        (price_cents / 100.0)::numeric(10, 2) as price_usd,
        discount_pct,

        -- each version was captured by one load
        dbt_valid_from as loaded_at,
        dbt_valid_from::date as snapshot_date

    from snapshot

)

select * from renamed
