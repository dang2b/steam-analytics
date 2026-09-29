-- Every catalogue game falls in exactly one owners bucket, so the shares
-- should add up to 1, give or take rounding. Passes while the mart is empty.
select sum(share_of_games) as games, sum(share_of_owners) as owners
from {{ ref('catalog_owners_distribution') }}
having abs(sum(share_of_games) - 1) > 0.01
    or abs(sum(share_of_owners) - 1) > 0.01
