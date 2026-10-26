"""Synthetic fixtures so CI runs every client adapter without downloading anything.

  --client usaspending  writes a CSV in the USAspending archive layout (same column names) for
                        ingestion/load_usaspending.py --csv, so the loader is tested too
  --client erp_sap      writes bronze.sap_invoice_lines   (BELNR, BUZEI, BUDAT, BUKRS, LIFNR, NAME1, KONZS, DMBTR, SGTXT)
  --client erp_oracle   writes bronze.oracle_ap_invoices  (INVOICE_ID, LINE_NUMBER, GL_DATE, VENDOR_NAME, INVOICE_AMOUNT, ...)

Every client shares the same suppliers, descriptions and amounts (seeded), including a long tail,
spelling variants of one supplier name and some negative lines (credits / de-obligations).

Usage
    python tests/fixtures/make_fixtures.py --client usaspending --csv data/fixture/contracts.csv
    python tests/fixtures/make_fixtures.py --client erp_sap --db warehouse/fixture.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

N = 2_000
DESCRIPTIONS = [
    ("Network server refresh and software licence", "7B22"), ("Road paving and bridge repair", "Y1LB"),
    ("Janitorial and custodial services", "S201"), ("Wildfire fuels reduction and habitat restoration", "F003"),
    ("Program management support services", "R408"), ("Helicopter charter for aviation support", "V121"),
    ("Office furniture and supplies", "7110"), ("Pickup truck purchase", "2310"),
    ("HVAC maintenance", "J041"), ("Hydrology research study", "AJ12"), ("Equipment rental", "W036"),
    ("Visitor centre construction", "Z2AA"),
]
UNITS = ["National Park Service", "Bureau of Land Management", "U.S. Geological Survey", "Fish and Wildlife Service"]


def base(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_sup = 300
    sup = rng.zipf(1.4, N) % n_sup  # a few large suppliers, long tail
    desc = rng.integers(0, len(DESCRIPTIONS), N)
    amount = np.round(rng.lognormal(9, 1.6, N), 2)
    amount[rng.random(N) < 0.12] *= -0.3  # credits / de-obligations
    names = [f"SUPPLIER {i:03d} INC" for i in range(n_sup)]
    raw = [names[s] if rng.random() > 0.3 else names[s].replace(" INC", ", INC.") for s in sup]
    return pd.DataFrame({
        "seq": np.arange(N), "sup": sup, "name": [names[s] for s in sup], "raw": raw,
        "parent": [s // 10 if s < 50 else s for s in sup],  # first 50 suppliers belong to 5 groups
        "unit": [UNITS[i] for i in rng.integers(0, len(UNITS), N)],
        "date": pd.Timestamp("2024-10-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D"),
        "desc": [DESCRIPTIONS[d][0] for d in desc], "psc": [DESCRIPTIONS[d][1] for d in desc],
        "amount": amount, "award": rng.integers(0, 600, N),
    })


def usaspending(df: pd.DataFrame) -> pd.DataFrame:
    fy = df.date.dt.year + (df.date.dt.month >= 10)
    return pd.DataFrame({
        "contract_transaction_unique_key": [f"T{i:06d}" for i in df.seq],
        "contract_award_unique_key": [f"A{a:05d}" for a in df.award],
        "award_id_piid": [f"P{a:05d}" for a in df.award], "modification_number": "0",
        "federal_action_obligation": df.amount, "action_date": df.date.dt.date, "action_date_fiscal_year": fy,
        "awarding_sub_agency_name": df.unit, "awarding_office_name": df.unit + " HQ",
        "recipient_uei": [f"UEI{s:09d}" for s in df.sup], "recipient_name": df.name, "recipient_name_raw": df.raw,
        "recipient_parent_uei": [f"UEI{p:09d}" for p in df.parent],
        "recipient_parent_name": [f"SUPPLIER {p:03d} INC" for p in df.parent],
        "transaction_description": df.desc, "prime_award_base_transaction_description": df.desc,
        "product_or_service_code": df.psc, "product_or_service_code_description": df.desc,
        "naics_code": "541330", "naics_description": "ENGINEERING SERVICES",
        "type_of_contract_pricing": "FIRM FIXED PRICE",
        "extent_competed": np.where(df.seq % 8 == 0, "NOT COMPETED", "FULL AND OPEN COMPETITION"),
        "contracting_officers_determination_of_business_size":
            np.where(df.sup % 2 == 0, "SMALL BUSINESS", "OTHER THAN SMALL BUSINESS"),
    })


def sap(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "BELNR": [f"51{a:08d}" for a in df.award], "BUZEI": [f"{i:03d}" for i in df.seq % 1000 + 1],
        "BUDAT": df.date.dt.date, "BUKRS": [u[:4].upper() for u in df.unit], "LIFNR": [f"V{s:07d}" for s in df.sup],
        "NAME1": df.raw, "KONZS": [f"G{p:07d}" for p in df.parent], "KONZS_NAME": [f"SUPPLIER {p:03d} INC" for p in df.parent],
        "DMBTR": df.amount, "SGTXT": df.desc,
    }).drop_duplicates(["BELNR", "BUZEI"])


def oracle(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "INVOICE_ID": 900000 + df.award, "LINE_NUMBER": df.seq, "GL_DATE": df.date.dt.date, "OPERATING_UNIT": df.unit,
        "VENDOR_ID": 1000 + df.sup, "VENDOR_NAME": df.raw, "PARENT_VENDOR_ID": 1000 + df.parent,
        "PARENT_VENDOR_NAME": [f"SUPPLIER {p:03d} INC" for p in df.parent],
        "INVOICE_AMOUNT": df.amount, "LINE_DESCRIPTION": df.desc,
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, choices=["usaspending", "erp_sap", "erp_oracle"])
    ap.add_argument("--db", default="warehouse/fixture.duckdb")
    ap.add_argument("--csv", type=Path, default=Path("data/fixture/contracts.csv"))
    args = ap.parse_args()
    df = base()
    if args.client == "usaspending":
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        usaspending(df).to_csv(args.csv, index=False)
        print(f"wrote {len(df):,} contract actions to {args.csv}")
        return
    table, out = ("sap_invoice_lines", sap(df)) if args.client == "erp_sap" else ("oracle_ap_invoices", oracle(df))
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute(f"create or replace table bronze.{table} as select * from out")
    print(f"wrote {len(out):,} rows to bronze.{table} in {args.db}")


if __name__ == "__main__":
    main()
