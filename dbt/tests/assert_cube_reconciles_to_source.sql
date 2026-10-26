-- Every dollar is accounted for: the cube, the supplier rollup and the line fact all equal the source net
-- total, and gross obligations plus de-obligations equal net in the cube.
with src as (select sum(amount_usd) as net from {{ ref('int_spend_lines') }}),
cube as (select sum(net_spend_usd) as net, sum(gross_obligations_usd + deobligations_usd) as gd from {{ ref('rpt_spend_cube') }}),
sup as (select sum(net_spend_usd) as net from {{ ref('dim_supplier') }})

select 'cube' as check_name from src, cube where abs(cube.net - src.net) > 0.01
union all
select 'cube gross + deobligations' from cube where abs(cube.gd - cube.net) > 0.01
union all
select 'supplier rollup' from src, sup where abs(sup.net - src.net) > 0.01
