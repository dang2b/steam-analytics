-- Fails if any parsed owners range is inverted, which would mean the
-- bucket format changed and the split_part parsing is reading it wrong.
select
    appid,
    owners_bucket,
    owners_min,
    owners_max
from {{ ref('stg_steamspy__games') }}
where owners_min > owners_max
