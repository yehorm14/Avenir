# yehor: backend (contract, catalogue, routes, live adapters)

- **Owner:** Yehor (human) / Claude (agents)
- **Branches:** `yehor/live-adapters` (Tasks 1-3), `yehor/catalogue` (Tasks 4-6); per-task branches `yehor/adzuna`, `yehor/llm`
- **PR:** #1 merged (contract v2). Next PRs: "yehor: live adapters", "yehor: catalogue, routes"
- **Status:** in progress (Sat 17 Oct, ~21:40)

## Task
Plan v2: `docs/superpowers/plans/2026-10-17-avenir-data-and-adapters.md`. Each task: implementer agent (tests first) →
reviewer agent → fixes; whole-branch review before each PR.

## Done so far
- Contract v2 merged to `main` (PR #1): Metric, Career join, catalogue/routes files, `load_data()`, ports with
  no-network defaults, mock catalogue and routes for the 20 ML demo SOCs.
- **Task 3, LLM explanation: done, reviewed.** `avenir_adapters.llm`: `LlmExplanation` (OpenAI-compatible
  `/chat/completions`), `writer_from_env()`. Falls back to the template if a number is not in the response, a notice is
  not copied verbatim, the text says "you should"/"don't", or the call fails. `.env.example` gains `LLM_BASE_URL`, `LLM_MODEL`.
- **Task 4, catalogue build: done, reviewed.** `avenir_etl.curated.load_curated` (fails naming every unverified /
  unknown-SOC / bad-subject row) and `avenir_etl.build` (`python -m avenir_etl.build` → `snapshots/catalogue.json`).
  `shortage` missing until the OiD file is loaded; `wellbeing`/`stress` missing (no data, cut order); `ads_now` filled live by the API.
- **Task 2, Adzuna live ads: built, in review fixes.** `avenir_adapters.adzuna.AdzunaAds`: live count, 10-min cache,
  snapshot fallback; fixing a hard 3 s deadline, a circuit breaker for outages, and logging.
  `scripts/fetch/adzuna_snapshot.py` now keys the snapshot by SOC.
- Tests on the branches: 62-66 passing, ruff clean.

## In progress / next
- Task 6, routes: `data/curated/routes.csv` (header only; humans add real routes), `load_routes`, CLI writes `routes.json`.
- Task 1, registry (`ads_source()`, `explanation_writer()`, `tag_suggester()`) once Task 2 passes review. Then the PR,
  and Nazar's API picks it up with no change (`deps.default_ports()`).
- Task 5, OiD shortage: blocked on the data download.

## Blocked on (humans)
- **Adzuna keys** in `.env` (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`), then `make adzuna` for the snapshot behind pull-the-plug.
- **LLM endpoint** (ELM?): base URL, key, model. Who has access? Without it the app uses the template text (fine).
- **Occupations in Demand** "Download all data (ZIP)" → `data/raw/oid/` (unblocks Task 5).
- **`data/curated/occupations.csv`**: fill `verified_by` (your name) and a one-line description for each of the 20 rows.
  The build refuses to run until every row is verified.
- **`data/curated/routes.csv`**: real Scottish routes (apprenticeships.scot, Graduate Apprenticeships, university course
  pages) with the page URL, at least for the likely picks. Needed by Sun 08:00.

## Open questions (for humans)
- Arsenii: public `ML.affinity()` and `ML.backtest_years()` (we use `ml._load` in `data.py` for now); pick rules for
  the backtest groups (balanced is null today); confirm the 20 demo careers.
- Team: who owns the frontend (AGENTS.md says TBD)? It can start now on `docs/contracts.md` + mock JSON.
- PR #2 duplicates the ML slice already on `main` (identical `packages/ml`, `snapshots/ml`) and conflicts: suggest closing.

## Decisions taken (change if wrong)
- Adzuna and LLM: 3 s total per call including the retry; Adzuna stops live calls for 60 s after an outage.
- Real catalogue/routes files are labelled "preliminary", never "mock".
- Wellbeing and stress stay missing tonight.

## Marked (verify)
- Occupations in Demand level labels; ELM API shape.
