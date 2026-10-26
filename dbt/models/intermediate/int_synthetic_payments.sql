-- SYNTHETIC: invoice and payment dates for each positive spend line. USAspending records obligations,
-- not invoices or payments, so payment timing is simulated deterministically (hash of line_id) to
-- demonstrate the working-capital analysis: 25% paid early (5-20 days), 65% on time (21-30), 10% late (31-75).
with base as (
    select
        line_id, org_unit, category, amount_usd, action_date,
        hash(line_id || 'inv') % 60                 as days_to_invoice,
        hash(line_id || 'pay') % 100                as u,
        hash(line_id || 'days') % 1000              as v
    from {{ ref('fct_spend_line') }}
    where is_obligation
)

select
    line_id, org_unit, category, amount_usd,
    action_date + cast(days_to_invoice as integer)                              as invoice_received_date,
    cast(case
        when u < 25 then 5 + v % 16
        when u < 90 then 21 + v % 10
        else 31 + v % 45
    end as integer)                                                             as days_to_pay
from base
