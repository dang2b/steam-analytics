with source as (

    select * from {{ source('raw', 'games') }}

),

renamed as (

    select
        {{ steamspy_game_columns() }},

        -- the loader upserts but never deletes, so games that dropped out of
        -- the top 100 keep an older loaded_at than the latest load
        loaded_at = max(loaded_at) over () as is_in_latest_top100,

        loaded_at

    from source

)

select * from renamed
