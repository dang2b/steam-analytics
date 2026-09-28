with games as (

    select * from {{ ref('stg_steamspy__games') }}

),

aggregated as (

    select
        -- SteamSpy lists co-publishers in one comma-separated string, and
        -- names like 'CAPCOM Co., Ltd.' contain commas too, so the string
        -- is grouped as-is rather than split
        publisher,

        count(*) as game_count,
        count(*) filter (where is_free) as free_game_count,
        sum(concurrent_users) as total_concurrent_users,
        sum(total_reviews) as total_reviews,

        -- weighted by review volume, so one small game can't swing the score
        round(
            sum(positive_reviews)::numeric / nullif(sum(total_reviews), 0),
            4
        ) as positive_review_ratio,

        (array_agg(game_name order by concurrent_users desc))[1] as top_game_by_ccu

    from games
    where is_in_latest_top100
    group by publisher

)

select
    *,
    rank() over (order by total_concurrent_users desc) as ccu_rank
from aggregated
