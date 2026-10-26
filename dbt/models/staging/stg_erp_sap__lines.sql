{{ config(enabled=var('client') == 'erp_sap') }}
-- Adapter: SAP-style invoice lines (LIFNR vendor, DMBTR amount, BUDAT posting date, SGTXT text). Calendar fiscal year.
select
    BELNR || '-' || BUZEI                                               as line_id,
    'erp_sap'                                                           as client,
    BELNR                                                               as award_id,
    cast(BUDAT as date)                                                 as action_date,
    year(cast(BUDAT as date))                                           as fiscal_year,
    'FY' || cast(year(cast(BUDAT as date)) as varchar) || ' Q' || cast(quarter(cast(BUDAT as date)) as varchar) as fiscal_quarter,
    BUKRS                                                               as org_unit,
    LIFNR                                                               as supplier_id,
    NAME1                                                               as supplier_name,
    NAME1                                                               as supplier_name_raw,
    coalesce(KONZS, LIFNR)                                              as parent_supplier_id,
    coalesce(KONZS_NAME, NAME1)                                         as parent_supplier_name,
    cast(DMBTR as decimal(18, 2))                                       as amount_usd,
    SGTXT                                                               as description,
    cast(null as varchar)                                               as psc_code,
    cast(null as varchar)                                               as naics_code,
    cast(null as varchar)                                               as extent_competed,
    cast(null as varchar)                                               as business_size
from {{ source('bronze', 'sap_invoice_lines') }}
