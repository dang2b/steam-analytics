-- SteamSpy's list has 100 games. More rows means games that dropped out of
-- the top 100 are leaking into the marts.
select count(*) as games
from {{ ref('game_rankings') }}
having count(*) > 100
