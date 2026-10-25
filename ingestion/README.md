# Ingestion (roadmap)

Loaders for the real data go here and write to the same `bronze` tables as the fixture.

Real data: [USAspending.gov](https://www.usaspending.gov/download_center/custom_award_data) federal contract awards or UK [Contracts Finder](https://www.contractsfinder.service.gov.uk/). Add a synthetic invoice and payment-terms table for DPO. CI uses a synthetic supplier and spend-line fixture with a keyword taxonomy.
