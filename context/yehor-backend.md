# yehor: backend (contract, catalogue, routes, live adapters)

- **Owner:** Yehor (human) / Claude (agents)
- **Branch:** `yehor/wave0-contracts` (PR #1), then `yehor/live-adapters`, `yehor/catalogue`
- **PR:** #1
- **Status:** ready for review (PR #1); next work planned, not started

## Task
Contract in code, built on Arsenii's ML contract; backend split with Nazar; then my plan v2.

## Done so far
- Ported Arsenii's ML slice from KATYATA #9 (his authorship kept): `packages/ml`, `snapshots/ml/mock`, `docs/decisions.md`.
- Contract v2 in `packages/contracts`: Metric = ML shape + region; Career joins ML occupation + catalogue; catalogue and routes files; `load_data()`; ports with no-network defaults (ML keyword suggester); mock catalogue and routes for the 20 ML demo SOCs.
- Plans v2: Nazar `docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md`, me `...-data-and-adapters.md`.
- `docs/contracts.md` v2, `docs/backend-split.md`, `prompts/nazar-claude.md`, `prompts/yehor-claude.md`.
- `data/curated/occupations.csv` pre-filled with the ML demo SOCs (verified_by empty).
- Tests: 32 passed (19 ML, 13 contract).

## Blocked on
- PR #1 merge (Yehor, on GitHub).

## Open questions (for humans)
- Arsenii: public `ML.affinity()` and `ML.backtest_years()` (we use `ml._load` in `data.py` for now); use the pick rules from Nazar's plan Task 5 for the backtest groups (balanced is null today).
- Team: confirm the 20 demo careers (Arsenii's set differs from the spec's list).
- LLM endpoint (spec says ELM); the adapter takes any OpenAI-compatible URL.

## Marked (verify)
- Occupations in Demand level labels; ELM API shape.

## Next step
Merge PR #1, send Nazar `prompts/nazar-claude.md`, continue in VS Code with `prompts/yehor-claude.md`.
