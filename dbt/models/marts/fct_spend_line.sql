-- One row per spend line with its category from the keyword taxonomy (the first matching rule wins).
select
    s.line_id,
    s.supplier_id,
    s.invoice_date,
    s.paid_date,
    s.amount_usd,
    s.payment_terms_days,
    {{ dbt.datediff('s.invoice_date', 's.paid_date', 'day') }}  as days_to_pay,
    t.category,
    t.sub_category
from {{ ref('stg_bronze__spend_lines') }} s
left join {{ ref('stg_bronze__taxonomy_rules') }} t
    on lower(s.description) like '%' || t.keyword || '%'
qualify row_number() over (partition by s.line_id order by t.keyword) = 1
