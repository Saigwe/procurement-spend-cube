-- Cumulative share rises to exactly 1, and the tail starts only after the head.
select spend_rank, cumulative_share
from {{ ref('rpt_supplier_pareto') }}
where cumulative_share > 1.000001
   or (is_tail and spend_rank = 1)
union all
select null, max(cumulative_share)
from {{ ref('rpt_supplier_pareto') }}
having abs(max(cumulative_share) - 1) > 1e-6
