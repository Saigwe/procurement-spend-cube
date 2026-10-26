# Design doc: Procurement Spend Cube & Supplier Analytics

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Core build complete |
| **Last updated** | 2026-10-26 |

## 1. Problem and users
- **Users:** category managers, procurement directors, finance (treasury) and the consultants who serve them.
- **Questions they need answered:** Where does the money go by category and unit? Which suppliers hold most of it? Which categories are fragmented enough to consolidate? How much is not competed? Are we paying early or late?
- **Current pain (scenario):** each new client sends a differently shaped ERP extract. Rebuilding the cube per client takes weeks, and numbers don't tie back to the ledger.

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | One standard spend line for every client; cube, Pareto, consolidation, competition and working-capital marts on top. |
| Data quality | Every dollar reconciles to source; at most 2% of gross obligations Unclassified; de-obligations kept separate from obligations. |
| Freshness / SLA | Batch: rebuild on each new extract. The full real year builds in about 2 s. |
| Scale | 42k lines today; at 10x and beyond, the same models run on a warehouse adapter (Snowflake/BigQuery) with incremental facts. |
| Cost | Runs on a laptop with DuckDB; CI is free GitHub Actions. |

## 3. Design
- **Layers:** bronze (raw, as delivered) → silver (client adapter, then standard spend line) → gold (facts and reports).
- **Key choices:** a `client` var selects one staging adapter, and only that one is enabled. The PSC taxonomy and keyword rules are seeds, so analysts change them without touching SQL. Suppliers are keyed on the registry ID (UEI) and rolled up to the parent.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| Multi-client | Fork per client; one project with adapters | Adapters + `client` var | One codebase, CI matrix proves every adapter. |
| Supplier identity | Fuzzy names; registry ID | Registry ID, names as fallback | Matching scored at best F1 0.71 against UEIs; shared names cap precision near 0.63. |
| Classification without codes | Keyword rules; TF-IDF model; LLM | TF-IDF model now, LLM on roadmap | Model 0.745 accuracy vs rules 0.226 on held-out awards. |
| Payment data | Omit DPO; synthetic payments | Synthetic, labelled | Shows the method; real clients supply invoice and payment dates. |

## 5. Risks and what I'd change at 10x scale
- Keyword rules are weak (58% precision when they fire): replace with the trained model or an LLM for clients without product codes, and keep a human review queue.
- Synthetic payment timing means the working-capital figures are illustrative only.
- At 10x: incremental `fct_spend_line`, a supplier master service with match review, and per-client schemas.
