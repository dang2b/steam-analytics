with source as (

    select * from {{ source('raw', 'friends') }}

),

renamed as (

    select
        steamid as steam_id,
        personaname as persona_name,
        profileurl as profile_url,
        personastate as persona_state_code,

        -- codes from the Steam Web API GetPlayerSummaries docs
        case personastate
            when 0 then 'offline'
            when 1 then 'online'
            when 2 then 'busy'
            when 3 then 'away'
            when 4 then 'snooze'
            when 5 then 'looking to trade'
            when 6 then 'looking to play'
            else 'unknown'
        end as persona_state,

        loaded_at

    from source

)

select * from renamed
