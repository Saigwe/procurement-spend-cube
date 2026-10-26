-- How much spend was competed, and how much went to small businesses, by category.
-- Only sources that record these fields (USAspending) populate the shares; ERP clients show nulls.
select
    category,
    sum(amount_usd) filter (where is_obligation)                                    as gross_obligations_usd,
    sum(amount_usd) filter (where is_obligation and (extent_competed like '%NOT %'
        or extent_competed like 'NON-COMPETITIVE%'))
        / nullif(sum(amount_usd) filter (where is_obligation and extent_competed is not null), 0) as not_competed_share,
    sum(amount_usd) filter (where is_obligation and business_size = 'SMALL BUSINESS')
        / nullif(sum(amount_usd) filter (where is_obligation and business_size is not null), 0)   as small_business_share
from {{ ref('fct_spend_line') }}
group by 1
