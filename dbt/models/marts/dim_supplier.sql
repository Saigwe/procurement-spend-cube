-- One row per parent supplier: how many registered entities and raw name spellings roll up into it.
select
    parent_supplier_id,
    any_value(parent_supplier_name)                     as parent_supplier_name,
    count(distinct supplier_id)                         as child_entities,
    count(distinct supplier_name_raw)                   as raw_name_variants,
    sum(amount_usd)                                     as net_spend_usd
from {{ ref('fct_spend_line') }}
group by 1
