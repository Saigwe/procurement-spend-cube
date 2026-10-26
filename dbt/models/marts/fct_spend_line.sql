-- One row per spend line with its category. Where the source has a federal Product and Service Code,
-- the category comes from it (longest matching prefix in seed psc_categories); otherwise from the
-- keyword rules (seed keyword_rules: lowest priority number wins, then the longest keyword).
with lines as (
    select * from {{ ref('int_spend_lines') }}
),

psc as (
    select l.line_id, p.category
    from lines l
    join {{ ref('psc_categories') }} p on starts_with(l.psc_code, p.psc_prefix)
    qualify row_number() over (partition by l.line_id order by length(p.psc_prefix) desc) = 1
),

kw as (
    select l.line_id, k.category
    from lines l
    join {{ ref('keyword_rules') }} k on contains(lower(l.description), k.keyword)
    qualify row_number() over (partition by l.line_id order by k.priority, length(k.keyword) desc, k.keyword) = 1
)

select
    l.*,
    p.category                                                  as psc_category,
    k.category                                                  as keyword_category,
    coalesce(p.category, k.category, 'Unclassified')            as category,
    case when p.category is not null then 'psc code'
         when k.category is not null then 'keyword rule'
         else 'unclassified' end                                as category_source,
    l.amount_usd > 0                                            as is_obligation,
    l.amount_usd < 0                                            as is_deobligation
from lines l
left join psc p on p.line_id = l.line_id
left join kw k on k.line_id = l.line_id
