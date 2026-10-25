-- Supplier Pareto: cumulative share of spend; the tail is suppliers outside the top 80% of spend.
with s as (
    select supplier_id, sum(amount_usd) as spend_usd, count(*) as lines,
           sum(amount_usd * days_to_pay) / sum(amount_usd) as weighted_days_to_pay
    from {{ ref('fct_spend_line') }}
    group by 1
)

select
    *,
    sum(spend_usd) over (order by spend_usd desc, supplier_id rows unbounded preceding) / sum(spend_usd) over () as cumulative_share,
    sum(spend_usd) over (order by spend_usd desc, supplier_id rows unbounded preceding) / sum(spend_usd) over () > 0.8 as is_tail_supplier
from s
