{{ config(enabled=var('client') == 'usaspending') }}
-- Adapter: USAspending contract actions -> standard spend lines. Federal fiscal year starts 1 October.
select
    contract_transaction_unique_key                                     as line_id,
    'usaspending'                                                       as client,
    contract_award_unique_key                                           as award_id,
    cast(action_date as date)                                           as action_date,
    cast(action_date_fiscal_year as integer)                            as fiscal_year,
    'FY' || action_date_fiscal_year || ' Q' || cast(
        (month(cast(action_date as date)) + 2) % 12 // 3 + 1 as varchar) as fiscal_quarter,
    awarding_sub_agency_name                                            as org_unit,
    recipient_uei                                                       as supplier_id,
    recipient_name                                                      as supplier_name,
    recipient_name_raw                                                  as supplier_name_raw,
    coalesce(nullif(recipient_parent_uei, ''), recipient_uei)          as parent_supplier_id,
    coalesce(nullif(recipient_parent_name, ''), recipient_name)        as parent_supplier_name,
    cast(federal_action_obligation as decimal(18, 2))                   as amount_usd,
    coalesce(nullif(transaction_description, ''), prime_award_base_transaction_description) as description,
    product_or_service_code                                             as psc_code,
    naics_code,
    extent_competed,
    contracting_officers_determination_of_business_size                 as business_size
from {{ source('bronze', 'contract_transactions') }}
