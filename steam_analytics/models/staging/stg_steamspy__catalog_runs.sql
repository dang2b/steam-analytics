with source as (

    select * from {{ source('raw', 'catalog_runs') }}

),

renamed as (

    select
        run_id,
        started_at,
        finished_at,
        finished_at is not null as is_finished,
        last_page + 1 as pages_loaded,
        list_size,
        -- counts every upsert, so a game seen on two pages counts twice
        games_loaded as games_upserted,
        round(extract(epoch from finished_at - started_at) / 3600, 2) as run_hours

    from source

)

select * from renamed
