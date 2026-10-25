select
    supplier_id,
    supplier_name,
    country_code
from {{ source('bronze', 'suppliers') }}
