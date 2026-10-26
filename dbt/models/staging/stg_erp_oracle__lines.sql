{{ config(enabled=var('client') == 'erp_oracle') }}
-- Adapter: Oracle Payables-style invoices (VENDOR_NAME, INVOICE_AMOUNT, GL_DATE, LINE_DESCRIPTION). Calendar fiscal year.
select
    cast(INVOICE_ID as varchar) || '-' || cast(LINE_NUMBER as varchar) as line_id,
    'erp_oracle'                                                        as client,
    cast(INVOICE_ID as varchar)                                         as award_id,
    cast(GL_DATE as date)                                               as action_date,
    year(cast(GL_DATE as date))                                         as fiscal_year,
    'FY' || cast(year(cast(GL_DATE as date)) as varchar) || ' Q' || cast(quarter(cast(GL_DATE as date)) as varchar) as fiscal_quarter,
    OPERATING_UNIT                                                      as org_unit,
    cast(VENDOR_ID as varchar)                                          as supplier_id,
    VENDOR_NAME                                                         as supplier_name,
    VENDOR_NAME                                                         as supplier_name_raw,
    cast(coalesce(PARENT_VENDOR_ID, VENDOR_ID) as varchar)              as parent_supplier_id,
    coalesce(PARENT_VENDOR_NAME, VENDOR_NAME)                           as parent_supplier_name,
    cast(INVOICE_AMOUNT as decimal(18, 2))                              as amount_usd,
    LINE_DESCRIPTION                                                    as description,
    cast(null as varchar)                                               as psc_code,
    cast(null as varchar)                                               as naics_code,
    cast(null as varchar)                                               as extent_competed,
    cast(null as varchar)                                               as business_size
from {{ source('bronze', 'oracle_ap_invoices') }}
