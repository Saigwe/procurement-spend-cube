select
    line_id,
    supplier_id,
    description,
    cast(invoice_date as date)                 as invoice_date,
    amount_usd,
    payment_terms_days,
    cast(paid_date as date)                    as paid_date
from {{ source('bronze', 'spend_lines') }}
