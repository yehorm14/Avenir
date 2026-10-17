# yehor: backend (contract, catalogue, routes, live adapters)

- **Owner:** Yehor (human) / Claude (agents); Codex runs the integration harness on `codex/*`
- **Status:** in progress (Sat 17 Oct, ~22:40). Four draft PRs open, all reviewed.

## Open PRs (all drafts, need a human review + merge)
| PR | Branch | What | Notes |
| --- | --- | --- | --- |
| #3 | `yehor/catalogue` | Catalogue + routes ETL (`python -m avenir_etl.build`) | Real build needs `verified_by` filled + real routes (Sun 08:00) |
| #4 | `yehor/contract-v1.1` | Contract v2.1: ML v1.1 additions; AGENTS.md rule 11 (snapshots/ml up to 5 MB) | **Needs Nazar's ack.** Merge before #6 |
| #5 | `yehor/live-adapters` | Registry, Adzuna (hard 3 s, breaker, snapshot fallback), LLM explanation (checked, template fallback) | Nazar's API picks it up with no change |
| #6 | `yehor/frontend-handoff` | `docs/frontend/`: README, JSON schemas, generated examples | Regenerate after #4 merges |

Suggested merge order: #4 → #5 → #3 → #6 (then regenerate #6's pack).

## Done
- Plan v2 Tasks 1, 2, 3, 4, 6: implemented test-first, reviewed per task, whole-branch reviewed.
- Contract v2.1 adopting Arsenii's ML v1.1 (from KATYATA `arsenii/ml-data` 03fb482; he pushes the data to Avenir himself).
- Codex integration run (21:58) with v1.1 overlaid: everything merges cleanly; 412 occupations / 20 demo careers
  load with no lost flags; one contract test assumed history starts in 2011 (v1.1: 2007) — being fixed on #4.

## Next
- Task 5 (Occupations in Demand → `shortage`): as soon as the OiD file is in `data/raw/oid/`.
- Regenerate the frontend pack after #4; add a recommendation example when Nazar's `recommend()` lands.
- Sun 08:00-10:00: real `snapshots/catalogue.json` + `routes.json`; `AVENIR_FREEZE=1 pytest`.

## Blocked on (humans)
- **Adzuna keys** in `.env`, then `python scripts/fetch/adzuna_snapshot.py` and commit `snapshots/adzuna/<date>.json`.
  Without it, pull-the-plug shows ads as "missing". **Demo blocker.**
- **Occupations in Demand** ZIP → `data/raw/oid/`.
- **LLM endpoint** (base URL, key, model); without it the template text is used (fine).
- **`data/curated/occupations.csv`**: `verified_by` + descriptions for the 20 rows; **`routes.csv`**: real Scottish routes with URLs. Save as "CSV UTF-8".
- Arsenii: push ML v1.1 to Avenir (5 MB exception in #4). Team: matcher labels for Arsenii; confirm the 20 demo careers.
- Close stale PR #2. Name the frontend owner in AGENTS.md.

## For Nazar (also in PR #4/#5)
- Copy `evidence` from HedgeCandidate into Hedge; regenerate `docs/openapi.json` after #4.
- Pin test fixtures to mocks: `load_data(ml_dir=<repo>/snapshots/ml/mock, ...)`.
- Overlay `ads_now` in parallel or warm the cache before the pitch; `/demo/live` doesn't switch off the LLM.
- Roadmap step 1 "Take Higher ..." needs a non-Scottish variant (routes carry `nation`).

## Marked (verify)
- Occupations in Demand level labels; ELM API shape; licence per route source page.
