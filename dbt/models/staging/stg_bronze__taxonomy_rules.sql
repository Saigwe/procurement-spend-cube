select
    keyword,
    category,
    sub_category
from {{ source('bronze', 'taxonomy_rules') }}
