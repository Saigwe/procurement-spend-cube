-- The standard spend-line shape every report is built on, from whichever client adapter is active
-- (var `client`). Onboarding a client = one staging adapter; nothing downstream changes.
{% set adapters = {'usaspending': 'stg_usaspending__lines', 'erp_sap': 'stg_erp_sap__lines',
                   'erp_oracle': 'stg_erp_oracle__lines'} %}
{% if var('client') not in adapters %}
    {{ exceptions.raise_compiler_error("Unknown client '" ~ var('client') ~ "'. Add an adapter in models/staging.") }}
{% endif %}
select * from {{ ref(adapters[var('client')]) }}
