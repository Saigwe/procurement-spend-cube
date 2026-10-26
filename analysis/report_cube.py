"""Writes results/spend_cube.md from the gold marts: headline totals, Pareto, consolidation, competition, working capital.

Usage: python analysis/report_cube.py --db warehouse/spend.duckdb --out results/spend_cube.md
"""
import argparse

import duckdb


def m(x):
    return f"${float(x) / 1e6:,.1f}M"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/spend.duckdb")
    ap.add_argument("--out", default="results/spend_cube.md")
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    one = lambda q: con.sql(q).fetchone()

    lines_, gross, deob, net, deob_n = one("""
        select count(*), sum(amount_usd) filter (where is_obligation), sum(amount_usd) filter (where is_deobligation),
               sum(amount_usd), count(*) filter (where is_deobligation) from gold.fct_spend_line""")
    psc_share = one("""select sum(abs(amount_usd)) filter (where category_source = 'psc code') / sum(abs(amount_usd))
                       from gold.fct_spend_line""")[0]
    sup, head, tail, tail_spend = one("""select count(*), count(*) filter (where not is_tail), count(*) filter (where is_tail),
                                         sum(net_spend_usd) filter (where is_tail) from gold.rpt_supplier_pareto""")
    not_comp, small = one("""
        select sum(amount_usd) filter (where is_obligation and (extent_competed like '%NOT %' or extent_competed like 'NON-COMPETITIVE%'))
                 / sum(amount_usd) filter (where is_obligation and extent_competed is not null),
               sum(amount_usd) filter (where is_obligation and business_size = 'SMALL BUSINESS')
                 / sum(amount_usd) filter (where is_obligation and business_size is not null)
        from gold.fct_spend_line""")
    paid, dpo, late, interest, float_ = one("""
        select sum(paid_usd), sum(paid_usd * days_payable) / sum(paid_usd), sum(paid_usd * paid_late_share) / sum(paid_usd),
               sum(late_interest_usd), sum(early_payment_float_usd) from gold.rpt_working_capital""")
    savings = one("select sum(illustrative_savings_usd) from gold.rpt_category_consolidation")[0]

    out = [
        "# Spend cube on USAspending FY2025 Department of the Interior contracts",
        "",
        f"- {lines_:,} contract actions: {m(gross)} gross obligations, {m(deob)} de-obligations ({deob_n:,} actions), {m(net)} net.",
        f"- {psc_share:.2%} of absolute spend categorised from the PSC code; the rest falls to keyword rules or Unclassified.",
        f"- {sup:,} parent suppliers with positive net spend: {head:,} ({head / sup:.1%}) make up 80% of spend; "
        f"the {tail:,}-supplier tail holds {m(tail_spend)}.",
        f"- Illustrative tail consolidation savings at 5% of tail spend: {m(savings)}.",
        f"- {not_comp:.1%} of obligations not competed; {small:.1%} to small businesses.",
        f"- Working capital (SYNTHETIC payment dates, 30-day terms): {dpo:.1f} days payable on {m(paid)}, "
        f"{late:.1%} paid late, ${interest:,.0f} late interest, {m(float_)} float released by paying early.",
        "",
        "## Category consolidation",
        "",
        "| Category | Net spend | Suppliers | Suppliers for 80% | Tail suppliers | Tail spend | Top supplier share |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for c, n, s, s80, t, ts, top in con.sql("""
            select category, net_spend_usd, suppliers, suppliers_for_80pct, tail_suppliers, tail_spend_usd, top_supplier_share
            from gold.rpt_category_consolidation order by net_spend_usd desc""").fetchall():
        out.append(f"| {c} | {m(n)} | {s:,} | {s80:,} | {t:,} | {m(ts)} | {top:.1%} |")
    out += ["", "## Competition by category", "", "| Category | Gross obligations | Not competed | Small business |", "|---|---:|---:|---:|"]
    for c, g, nc, sb in con.sql("""select category, gross_obligations_usd, not_competed_share, small_business_share
                                   from gold.rpt_competition where gross_obligations_usd is not null
                                   order by gross_obligations_usd desc""").fetchall():
        out.append(f"| {c} | {m(g)} | {nc:.1%} | {sb:.1%} |")
    open(args.out, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
