# yehor: backend (contract, ETL, live adapters)

- **Owner:** Yehor (human) / Claude (agents)
- **Branch:** `yehor/wave0-contracts`, then `yehor/<topic>`
- **PR:** contract PR (this one)
- **Status:** in progress

## Task
Contract in code, backend split with Nazar, then the ETL and live adapters plan.

## Done so far
- `packages/contracts`: models, metric, envelope, snapshot formats, ports with safe defaults, mock generator (tests green).
- `snapshots/mock/` generated (source MOCK, SOC 00NN).
- Plans: `docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md` (Nazar), `...-data-and-adapters.md` (Yehor).
- `docs/backend-split.md`, `prompts/nazar-claude.md`.

## Blocked on
- Real data downloads (laptop; this cloud workspace cannot reach ONS, Nomis, ILO, ESCO).

## Open questions (for humans)
- Confirm the 20 occupations and fill SOC 2020 codes in `data/curated/occupations.csv`.
- Which LLM endpoint (spec says "ELM"); the adapter takes any OpenAI-compatible URL.

## Marked (verify)
- ASHE table number for annual gross pay (14.7a) and the age band for early-career pay.
- Occupations in Demand level labels.

## Next step
Merge the contract PR, send Nazar `prompts/nazar-claude.md`, start plan Tasks 1 to 3.
