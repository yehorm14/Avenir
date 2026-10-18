# Context: arsenii/ml-data

- **Owner:** Arsenii Harbar (z1nare; agent: Claude)
- **Status:** ready for review
- **Draft PR:** KATYATA #9, ported to Avenir in #1
- **Task-list item:** ML slice: contracts and mocks for the team; data pipeline

## What this branch does
Hands the team the ML slice's contract and mocks, so the backend, decision layer and UI can build now: `packages/ml/CONTRACTS.md` (artefact shapes, flags, confidence rules, Python interface), JSON Schemas, the stdlib-only `pathfinder_ml` loader with mock fallback, 19 contract tests, and `snapshots/ml/mock/*.json`, many already populated with preliminary real values. Also adds the data pipeline built so far (ASHE 2011-2025, SOC crosswalks, coding index, ILO exposure, CPIH), the probes and their findings, the slice description (`packages/ml/README.md`), the cluster runbook and five decisions in `docs/decisions.md`.

## Why it matters
Every card in the demo shows ML evidence (pay, real pay path, demand, exposure, resilience, hedge, fit, track record). With the contract and mocks on main, nobody waits for models.

## Files and areas it will touch
- `packages/ml/` (new: CONTRACTS.md, README.md, RUNBOOK.md, pathfinder_ml/, schemas/, scripts/, tests/)
- `snapshots/ml/mock/` (new)
- `docs/decisions.md` (five lines appended)
- `status/arsenii.md`
- `context/arsenii-ml-data.md` (this file)

## Out of scope
No edits to `docs/contracts.md` or `AGENTS.md` (Yehor's). No raw data in git (`data/` is gitignored). No trained models yet: hedges and fit affinities are placeholders until ESCO and the human labels arrive.

## Depends on / blocks
Depends on: PR #8 (Pathfinder design). Blocks: backend, decision layer and UI work that reads ML artefacts (they can start on the mocks now).

## Log
- 2026-10-17: loaded ASHE 2011-2025, SOC crosswalks, coding index, ILO index and CPIH locally; ran the probes (bridging seam, job-count noise, naive backtest, ISCO spread, COVID); the user decided exposure, demand, return, track record and self-employed coverage; wrote the contract, schemas, loader, tests and mocks; 19 tests pass. Next: final artefacts for all occupations, then hedges and the matcher after the ESCO download.
- 2026-10-18 (docs only, branch `arsenii/ml-docs-final`): documented the backtest `group_then` values, including `other`, in `packages/ml/README.md` (asked by Nazar on #9). Filled the source URLs checked online in `data/manifest.yaml` (CPIH, SOC 2000-2010 tables, SOC 2020 coding index, DfE AI annex, ONS job adverts, APS 2016 ad hoc, O*NET, ASHE 2007-2010 page), set the ILO WP140 licence to CC BY 4.0 with DOI, citation and the ILO adaptation disclaimer, and added a National Careers Service entry. The disclaimer is now also in `docs/data-sources.md` and the root README. `licence_checked_by` stays empty for a person to fill. Still (verify): ESCO licence; Nomis OGL version; whether ad hoc 006998 is APS; the licence of the ESCO to O*NET-SOC crosswalk; the geography of the NCS salaries. The in-app ILO credit and `snapshots/ml/sources.json` attribution do not yet carry the exact ILO disclaimer (code and snapshot, outside this docs-only change). `data/` is Yehor's folder (AGENTS.md section 3), so he should review the manifest change.
