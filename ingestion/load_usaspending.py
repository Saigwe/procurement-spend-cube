"""Load a USAspending contracts archive (one agency, one fiscal year) into DuckDB `bronze.contract_transactions`.

Each row is a contract action (award or modification) with its obligation, date, recipient (raw name,
cleaned name, unique entity id and parent), product/service code (PSC), NAICS and free-text description.
Source (public, no sign-in): https://files.usaspending.gov/award_data_archive/  e.g.
    FY2025_014_Contracts_Full_<date>.zip  (Department of the Interior, fiscal year 2025)

Only the ~20 columns this project uses are kept (the file has 297).

Usage
    python ingestion/load_usaspending.py --db warehouse/spend.duckdb --zip data/raw/FY2025_014_Contracts_Full.zip
    python ingestion/load_usaspending.py --db warehouse/fixture.duckdb --csv data/fixture/contracts.csv
"""
from __future__ import annotations

import argparse
import time
import zipfile
from pathlib import Path

import duckdb

COLUMNS = [
    "contract_transaction_unique_key", "contract_award_unique_key", "award_id_piid", "modification_number",
    "federal_action_obligation", "action_date", "action_date_fiscal_year", "awarding_sub_agency_name",
    "awarding_office_name", "recipient_uei", "recipient_name", "recipient_name_raw", "recipient_parent_uei",
    "recipient_parent_name", "transaction_description", "prime_award_base_transaction_description",
    "product_or_service_code", "product_or_service_code_description", "naics_code", "naics_description",
    "type_of_contract_pricing", "extent_competed", "contracting_officers_determination_of_business_size",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/spend.duckdb")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", type=Path)
    src.add_argument("--csv", type=Path)
    args = ap.parse_args()

    if args.zip:
        out = args.zip.with_suffix("")
        if not out.exists():
            with zipfile.ZipFile(args.zip) as z:
                z.extractall(out)
        files = sorted(p.as_posix() for p in out.rglob("*.csv"))
    else:
        files = [args.csv.as_posix()]

    t0 = time.perf_counter()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(args.db) as con:
        header = [d[0] for d in con.execute(f"select * from read_csv({files[:1]!r}, header=true, all_varchar=true) limit 0").description]
        missing = [c for c in COLUMNS if c not in header]
        if missing:
            raise SystemExit(f"missing columns: {missing}")
        con.execute("create schema if not exists bronze")
        con.execute(f"""
            create or replace table bronze.contract_transactions as
            select {', '.join(COLUMNS)}
            from read_csv({files!r}, header=true, all_varchar=true, union_by_name=true)""")
        rows, awards, recips, total = con.execute("""
            select count(*), count(distinct contract_award_unique_key), count(distinct recipient_uei),
                   sum(try_cast(federal_action_obligation as double))
            from bronze.contract_transactions""").fetchone()
    print(f"bronze.contract_transactions {rows:,} actions, {awards:,} awards, {recips:,} recipients, "
          f"${total / 1e9:,.2f}B net obligations ({time.perf_counter() - t0:.1f}s)")


if __name__ == "__main__":
    main()
