-- Parent suppliers ranked by net spend, with cumulative share. "Tail" = outside the top pareto_share of spend.
-- Suppliers with zero or negative net spend (only de-obligations this year) are listed but not ranked.
with s as (
    select parent_supplier_id, parent_supplier_name, child_entities, raw_name_variants, net_spend_usd
    from {{ ref('dim_supplier') }}
),

ranked as (
    select
        *,
        row_number() over (order by net_spend_usd desc, parent_supplier_id)                       as spend_rank,
        sum(net_spend_usd) over (order by net_spend_usd desc, parent_supplier_id rows unbounded preceding)
            / sum(net_spend_usd) over ()                                                           as cumulative_share
    from s
    where net_spend_usd > 0
)

select
    *,
    cumulative_share - net_spend_usd / sum(net_spend_usd) over () >= {{ var('pareto_share') }} as is_tail
from ranked
