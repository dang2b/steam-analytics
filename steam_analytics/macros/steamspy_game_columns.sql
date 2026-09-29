{#
    The cleaned columns shared by the two SteamSpy raw tables, games (top 100)
    and games_catalog (full catalogue), which have the same columns. Keeping
    the parsing in one place means a fix applies to both models.
#}
{% macro steamspy_game_columns() %}
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

        -- SteamSpy reports playtime in minutes, but currently returns 0 for
        -- every game (it no longer collects playtime), so 0 means unknown
        nullif(average_playtime_forever, 0) as avg_playtime_forever_minutes,
        nullif(average_playtime_2weeks, 0) as avg_playtime_2weeks_minutes,
        nullif(median_playtime_forever, 0) as median_playtime_forever_minutes,
        nullif(median_playtime_2weeks, 0) as median_playtime_2weeks_minutes,

        (price_cents / 100.0)::numeric(10, 2) as price_usd,
        (initial_price_cents / 100.0)::numeric(10, 2) as initial_price_usd,
        discount_pct,
        price_cents = 0 as is_free,

        concurrent_users
{%- endmacro %}
