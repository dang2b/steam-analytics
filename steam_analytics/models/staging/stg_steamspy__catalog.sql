with source as (

    select * from {{ source('raw', 'games_catalog') }}

),

latest_finished_run as (

    select max(started_at) as started_at
    from {{ source('raw', 'catalog_runs') }}
    where finished_at is not null

),

renamed as (

    select
        {{ steamspy_game_columns() }},

        -- every page commits separately, so each has its own loaded_at and
        -- max(loaded_at) can't mark the latest load. Rows written since the
        -- latest finished run started are current; games no longer in the
        -- catalogue keep an older loaded_at. False until a run finishes
        coalesce(source.loaded_at >= latest_finished_run.started_at, false)
            as is_in_latest_catalog,

        source.loaded_at

    from source
    cross join latest_finished_run

)

select * from renamed
