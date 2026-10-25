-- Every spend line must land in a category (an unclassified line means a taxonomy gap).
select line_id from {{ ref('fct_spend_line') }} where category is null
