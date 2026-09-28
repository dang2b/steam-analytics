with history as (

    select * from {{ ref('stg_steamspy__games_history') }}

),

-- if the pipeline ran more than once in a day, keep that day's last load
latest_per_day as (

    select
        *,
        row_number() over (
            partition by appid, snapshot_date
            order by loaded_at desc
        ) as load_rank
    from history

)

select
    appid,
    snapshot_date,
    game_name,
    concurrent_users,
    round(
        positive_reviews::numeric / nullif(positive_reviews + negative_reviews, 0),
        4
    ) as positive_review_ratio,
    price_usd,
    discount_pct,
    discount_pct > 0 as is_discounted
from latest_per_day
where load_rank = 1
