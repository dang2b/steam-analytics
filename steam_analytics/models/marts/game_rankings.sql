with games as (

    select * from {{ ref('stg_steamspy__games') }}

),

enriched as (

    select
        appid,
        game_name,
        developer,
        publisher,

        owners_min,
        owners_max,
        (owners_min + owners_max) / 2 as owners_estimate,

        concurrent_users,
        total_reviews,
        positive_review_ratio,

        price_usd,
        initial_price_usd,
        discount_pct,
        is_free,
        discount_pct > 0 as is_discounted,
        -- the loader stores a missing price as null; without this branch it
        -- would fall through to the else and look like a $30+ game
        case
            when price_usd is null then 'unknown'
            when is_free then 'free'
            when price_usd < 10 then 'under $10'
            when price_usd < 30 then '$10 to $30'
            else '$30 and up'
        end as price_tier,

        loaded_at

    from games
    where is_in_latest_top100

),

ranked as (

    select
        *,
        rank() over (order by concurrent_users desc) as ccu_rank,
        rank() over (order by positive_review_ratio desc nulls last) as review_score_rank
    from enriched

)

select * from ranked
