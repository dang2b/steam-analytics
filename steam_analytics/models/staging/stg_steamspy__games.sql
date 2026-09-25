with source as (

    select * from {{ source('raw', 'games') }}

),

renamed as (

    select
        appid,
        name as game_name,
        developer,
        publisher,

        -- owners arrives as a bucket like '20,000,000 .. 50,000,000'
        owners as owners_bucket,
        replace(split_part(owners, ' .. ', 1), ',', '')::bigint as owners_min,
        replace(split_part(owners, ' .. ', 2), ',', '')::bigint as owners_max,

        positive_reviews,
        negative_reviews,
        positive_reviews + negative_reviews as total_reviews,
        round(
            positive_reviews::numeric
            / nullif(positive_reviews + negative_reviews, 0),
            4
        ) as positive_review_ratio,

        -- SteamSpy reports playtime in minutes
        average_playtime_forever as avg_playtime_forever_minutes,
        average_playtime_2weeks as avg_playtime_2weeks_minutes,
        median_playtime_forever as median_playtime_forever_minutes,
        median_playtime_2weeks as median_playtime_2weeks_minutes,

        (price_cents / 100.0)::numeric(10, 2) as price_usd,
        (initial_price_cents / 100.0)::numeric(10, 2) as initial_price_usd,
        discount_pct,
        price_cents = 0 as is_free,

        concurrent_users,
        loaded_at

    from source

)

select * from renamed
