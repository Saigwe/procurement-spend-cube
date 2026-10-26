-- At most 2% of gross obligations may be left unclassified (a taxonomy gap to fix, not to ignore).
select
    sum(amount_usd) filter (where category = 'Unclassified') / sum(amount_usd) as unclassified_share
from {{ ref('fct_spend_line') }}
where is_obligation
having sum(amount_usd) filter (where category = 'Unclassified') / sum(amount_usd) > 0.02
