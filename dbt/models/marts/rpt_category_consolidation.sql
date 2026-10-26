-- Per category: how concentrated spend is, how much sits with tail suppliers, and an illustrative
-- consolidation saving (addressable_tail_savings x tail spend; an assumption, not a measured result).
with sup as (
    select category, parent_supplier_id, sum(amount_usd) as spend
    from {{ ref('fct_spend_line') }}
    group by 1, 2
    having sum(amount_usd) > 0
),

ranked as (
    select
        *,
        sum(spend) over (partition by category order by spend desc, parent_supplier_id rows unbounded preceding)
            / sum(spend) over (partition by category) as cum_share,
        spend / sum(spend) over (partition by category) as share
    from sup
)

select
    category,
    count(*)                                                                    as suppliers,
    sum(spend)                                                                  as net_spend_usd,
    count(*) filter (where cum_share - share < {{ var('pareto_share') }})      as suppliers_for_80pct,
    count(*) filter (where cum_share - share >= {{ var('pareto_share') }})     as tail_suppliers,
    sum(spend) filter (where cum_share - share >= {{ var('pareto_share') }})   as tail_spend_usd,
    max(share)                                                                  as top_supplier_share,
    coalesce(sum(spend) filter (where cum_share - share >= {{ var('pareto_share') }}), 0)
        * {{ var('addressable_tail_savings') }}                                 as illustrative_savings_usd
from ranked
group by 1
