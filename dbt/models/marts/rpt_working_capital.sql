-- Payment timing against terms, by organisation unit, on the SYNTHETIC payments (see int_synthetic_payments).
--   days_payable (spend-weighted days to pay) is the DPO view of the same behaviour.
--   paid_late_share / interest: late payments owe Prompt Payment Act interest (rate is an assumption here).
--   early_payment_float: cash released on average if early payments were made on the due date instead.
{% set terms = var('payment_terms_days') %}
{% set rate = var('annual_cost_of_capital') %}
select
    org_unit,
    sum(amount_usd)                                                             as paid_usd,
    sum(amount_usd * days_to_pay) / sum(amount_usd)                             as days_payable,
    sum(amount_usd) filter (where days_to_pay > {{ terms }}) / sum(amount_usd)   as paid_late_share,
    sum(amount_usd) filter (where days_to_pay < 20) / sum(amount_usd)            as paid_early_share,
    coalesce(sum(amount_usd * {{ rate }} * (days_to_pay - {{ terms }}) / 365.0)
        filter (where days_to_pay > {{ terms }}), 0)                           as late_interest_usd,
    coalesce(sum(amount_usd * ({{ terms }} - days_to_pay) / 365.0)
        filter (where days_to_pay < {{ terms }}), 0)                           as early_payment_float_usd
from {{ ref('int_synthetic_payments') }}
group by 1
