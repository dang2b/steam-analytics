select appid, snapshot_date, count(*) as rows
from {{ ref('game_daily_stats') }}
group by appid, snapshot_date
having count(*) > 1
