{{ config(severity='warn') }}

-- Warns when the latest catalogue run saw too few of the games in SteamSpy's
-- list. Some loss is expected (see catalog_coverage); a lot means the run was
-- slow or interrupted for long, so more games moved between pages.
select run_id, list_size, distinct_games, coverage
from {{ ref('catalog_coverage') }}
where coverage < {{ var('min_catalog_coverage', 0.9) }}
