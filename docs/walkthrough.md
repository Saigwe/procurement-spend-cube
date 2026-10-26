# 3-minute walkthrough: Procurement Spend Cube & Supplier Analytics

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, dbt/models, results/spend_cube.md, results/supplier_matching.md, GitHub Actions (matrix).

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | You can't negotiate what you can't see. This is a spend cube on $7.48 billion of real federal contract spend. It shows that 497 of 8,144 suppliers hold 80% of spend, and the tail where consolidation starts holds $1.36 billion. |
| 0:20–0:45 | README intro and the Data section | At a global management consultancy I delivered modular procurement analytics (spend, category insights, supplier negotiation, working capital) deployed to many clients a year. This rebuilds it on USAspending data. No client data is used. |
| 0:45–1:10 | README architecture and the client adapters | Each client extract maps to one standard spend line through a small adapter. USAspending, SAP-style and Oracle-style extracts all run in a CI matrix. |
| 1:10–1:35 | `results/supplier_matching.md` | Supplier name matching is scored against registry IDs. Fuzzy matching lifts recall from 0.77 to 0.82, but shared names cap precision, so suppliers are keyed on the ID. |
| 1:35–2:00 | `results/classification.md` and `results/spend_cube.md` | A text classifier reaches 0.745 accuracy against official category codes, against 0.226 for keyword rules. |
| 2:00–2:30 | The reconciliation test and the Pareto in Numbers | Every dollar reconciles back to source in a test. 31 dbt checks run in about 2 seconds. |
| 2:30–2:45 | `docs/design_doc.md`, the options table | The decision I'd defend in an interview: Score matching and classification against real ground truth before using them, rather than eyeballing a sample. |
| 2:45–3:00 | Back to the README top | For a procurement leader, that means where to consolidate, by how much, and how confident to be. The repo, numbers and design doc are linked under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `make fixture-all` once before recording, so CI-style output is fresh if you show it.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud wherever the README labels data as synthetic.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
