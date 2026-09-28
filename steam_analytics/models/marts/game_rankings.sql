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
        case
            when is_free then 'free'
            when price_usd < 10 then 'under $10'
            when price_usd < 30 then '$10 to $30'
            else '$30 and up'
        end as price_tier,

        loaded_at

    from games

),

ranked as (

    select
        *,
        rank() over (order by concurrent_users desc) as ccu_rank,
        rank() over (order by positive_review_ratio desc nulls last) as review_score_rank
    from enriched

)

select * from ranked
