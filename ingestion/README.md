# Ingestion

`load_usaspending.py` loads one USAspending contracts archive (one agency, one fiscal year) into
`bronze.contract_transactions`, keeping the 23 columns the models use out of 297. Each row is one contract action.

Source (public, no sign-in): [files.usaspending.gov/award_data_archive](https://files.usaspending.gov/award_data_archive/).
This project uses `FY2025_014_Contracts_Full_20261006.zip` (Department of the Interior, FY2025, 15.8 MB zipped, 96 MB CSV).

```bash
make download   # or fetch the zip into data/raw/ yourself
python ingestion/load_usaspending.py --db warehouse/spend.duckdb --zip data/raw/FY2025_014_Contracts_Full.zip
```

Other clients arrive as ERP extracts (`bronze.sap_invoice_lines`, `bronze.oracle_ap_invoices`). CI generates
synthetic ones with `tests/fixtures/make_fixtures.py`; each has its own staging adapter in `dbt/models/staging`.
