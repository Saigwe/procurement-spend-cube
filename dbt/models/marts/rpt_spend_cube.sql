-- The spend cube: category x organisation unit x fiscal quarter. Gross obligations and de-obligations
-- are kept apart (a net figure alone hides cancelled or reduced awards).
select
    category,
    org_unit,
    fiscal_quarter,
    count(*)                                                    as lines,
    count(distinct parent_supplier_id)                          as suppliers,
    sum(case when is_obligation then amount_usd else 0 end)     as gross_obligations_usd,
    sum(case when is_deobligation then amount_usd else 0 end)   as deobligations_usd,
    sum(amount_usd)                                             as net_spend_usd
from {{ ref('fct_spend_line') }}
group by 1, 2, 3
