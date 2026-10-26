PY ?= python
DB ?= warehouse/spend.duckdb
CLIENT ?= usaspending
ZIP ?= data/raw/FY2025_014_Contracts_Full.zip
DBT = cd dbt && DUCKDB_PATH=../$(DB) dbt

.PHONY: all download load dbt analysis fixture-all fixture clean

all: load dbt analysis   ## real USAspending data (run `make download` once first)

download:   ## Department of the Interior, FY2025, ~16 MB
	mkdir -p data/raw
	curl -L -o $(ZIP) https://files.usaspending.gov/award_data_archive/FY2025_014_Contracts_Full_20261006.zip

load:
	$(PY) ingestion/load_usaspending.py --db $(DB) --zip $(ZIP)

dbt:
	$(DBT) seed --profiles-dir . --full-refresh --vars '{client: $(CLIENT)}'
	$(DBT) build --profiles-dir . --vars '{client: $(CLIENT)}'

analysis:
	$(PY) analysis/report_cube.py --db $(DB)
	$(PY) analysis/match_suppliers.py --db $(DB)
	$(PY) analysis/classify_spend.py --db $(DB)

fixture-all:   ## synthetic fixture for one client adapter, no download (CI: CLIENT=usaspending|erp_sap|erp_oracle)
	$(MAKE) fixture dbt DB=warehouse/fixture_$(CLIENT).duckdb CLIENT=$(CLIENT)

fixture:
ifeq ($(CLIENT),usaspending)
	$(PY) tests/fixtures/make_fixtures.py --client usaspending --csv data/fixture/contracts.csv
	$(PY) ingestion/load_usaspending.py --db $(DB) --csv data/fixture/contracts.csv
else
	$(PY) tests/fixtures/make_fixtures.py --client $(CLIENT) --db $(DB)
endif

clean:
	rm -rf warehouse dbt/target dbt/logs data/fixture
