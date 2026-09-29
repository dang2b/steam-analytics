-- A streak can't hold more snapshots than the calendar days it spans (one
-- row per game per day), and it can't end before it starts.
select appid, unchanged_since, last_snapshot_date, snapshots_unchanged, days_unchanged
from {{ ref('game_freshness') }}
where snapshots_unchanged > days_unchanged
   or last_snapshot_date < unchanged_since
