-- Spend by category, sub-category and quarter.
select
    category,
    sub_category,
    cast({{ dbt.date_trunc('quarter', 'invoice_date') }} as date) as quarter_start,
    count(*)                    as lines,
    count(distinct supplier_id) as suppliers,
    sum(amount_usd)             as spend_usd
from {{ ref('fct_spend_line') }}
group by 1, 2, 3
