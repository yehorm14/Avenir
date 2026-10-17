# Avenir Catalogue, Routes and Live Adapters Implementation Plan (Yehor), v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the catalogue (`snapshots/catalogue.json`), the routes (`snapshots/routes.json`) and the live adapters (Adzuna ads, LLM explanation, tag suggester) that the API plugs in through `avenir_contracts.ports`.

**Architecture:** Arsenii's ML slice now produces pay, demand, exposure, resilience, hedges, fit and the backtest (`packages/ml/CONTRACTS.md` section 3). My ETL keeps only the display catalogue: friendly title, aliases, description, entry subjects, `shortage`, `wellbeing`, `stress`, plus routes. `packages/adapters/avenir_adapters/` holds the parsers and live adapters; `avenir_adapters.registry` exposes `ads_source()`, `explanation_writer()`, `tag_suggester()`, which Nazar's `deps.default_ports()` imports automatically. `packages/etl/avenir_etl/build.py` writes `CatalogueFile` and `RoutesFile`.

**Tech Stack:** Python 3.12, pandas, requests, Pydantic v2, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-avenir-design.md` sections 3, 6, 8; `packages/ml/CONTRACTS.md` (flags, `MUST_MENTION`); contract code `packages/contracts/avenir_contracts/` (`catalogue.py`, `ports.py`, `vocab.CATALOGUE_METRICS`).

## Global Constraints

- AGENTS.md applies. Never invent a value, code or URL; unparseable → `Metric.missing(...)` with a note.
- Catalogue metric units: `vocab.CATALOGUE_METRICS`. `wellbeing` and `stress` are `granularity="major_group"` and never presented as occupation-level.
- Live adapters: 3 s timeout, 1 retry, never raise, snapshot fallback with status `snapshot`.
- LLM prose cites only numbers in the response and includes every sentence in `rec.notices`; otherwise the template is used.
- Only my folders: `packages/adapters/`, `packages/etl/`, `packages/contracts/`, `scripts/fetch/`, `data/`.
- Parser tests use small committed fixtures in `packages/etl/tests/fixtures/`, never `data/raw/`.

## Review Focus

1. Adzuna slow, down or out of quota on stage → snapshot value within 3 s, status `snapshot`. Test in Task 2.
2. LLM text with a number not in the response (e.g. "£57,000" when pay is £56,914) or missing a notice → template used. Test in Task 3.
3. A curated row without `verified_by` or with a SOC not in the ML demo set → build fails, naming the row. Test in Task 4.
4. Occupations in Demand cell `x`, `c` or `z` → `shortage` missing, not 0. Test in Task 5.
5. A route for a nation the student isn't in is never offered as theirs (roadmap filters by nation; routes carry `nation`). Test in Task 6.

---

### Task 1: Registry
**Files:** `avenir_adapters/registry.py`, `packages/etl/tests/test_registry.py`
**Interfaces:** `tag_suggester() -> TagSuggester` (contract `KeywordSuggester`, i.e. ML's `match_tags`; swap to Arsenii's matcher when he ships it), `ads_source() -> AdsSource` (Task 2, falls back to `SnapshotAds`), `explanation_writer() -> ExplanationWriter` (Task 3, falls back to `TemplateExplanation`). Singletons; no network at import.
- [ ] Test: each returns an object satisfying its Protocol with no env vars set. Implement, pass, commit.

### Task 2: Adzuna live ads
**Files:** `avenir_adapters/adzuna/source.py`, `packages/etl/tests/test_adzuna.py`
**Interfaces:** `AdzunaAds(app_id: str | None, app_key: str | None, snapshot_dir: Path)` implements `AdsSource`. Live when keys exist and `set_live(True)` (default on with keys). Query `what` = catalogue title; 3 s timeout, 1 retry; 10-minute cache per SOC. Fallback: latest `snapshots/adzuna/*.json` entry for that SOC → `career.metrics["ads_now"]` → `Metric.missing`. Metric: `unit="count"`, `source="adzuna"`, `granularity="estimate"`, `confidence="medium"`, `note="Jobs by Adzuna: live ads matching the job title."`. Update `scripts/fetch/adzuna_snapshot.py` to key by SOC from `data/curated/occupations.csv`.
- [ ] Tests with `requests` monkeypatched: timeout → snapshot within the deadline; `set_live(False)` never calls the network; success → `live`. Implement, pass, commit.

### Task 3: LLM explanation with checks
**Files:** `avenir_adapters/llm/writer.py`, `packages/etl/tests/test_llm.py`
**Interfaces:** `LlmExplanation(base_url, api_key, model)` implements `ExplanationWriter` against an OpenAI-compatible `/chat/completions` (env `LLM_ENABLED`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`; ELM details to verify with the key). `allowed_numbers(rec) -> set[str]` (every number in `rec` in the formats the template uses); `numbers_in(text) -> set[str]`; reject if any number is not allowed or any `rec.notices` sentence's key idea is absent (check by exact sentence inclusion: the prompt tells the model to copy notices verbatim). Prompt: plain English for a 17-year-old, under 120 words, "worth exploring", no "you should" or "don't". Success → `ai_written=True`, `cited_numbers` filled.
- [ ] Tests: invented number → template; missing notice → template; `LLM_ENABLED=false` → template with no network call. Implement, pass, commit.

### Task 4: Catalogue ETL
**Files:** `data/curated/occupations.csv` (one row per ML demo SOC), `packages/etl/avenir_etl/curated.py`, `packages/etl/avenir_etl/build.py`, `packages/etl/tests/test_build.py`
**Interfaces:** `load_curated(csv: Path, demo_socs: set[str]) -> list[CatalogueEntry]` (fails on empty `verified_by`, unknown SOC, or a subject outside `vocab.SUBJECTS`, naming the row; list columns split on `|`); `build_catalogue(curated, oid_csv | None, wellbeing_csv | None, stress_csv | None) -> CatalogueFile`; CLI `python -m avenir_etl.build` writes `snapshots/catalogue.json` and `snapshots/routes.json`; any absent input → `Metric.missing` for that key.
- [ ] Team fills `title, aliases, description, entry_subjects, verified_by` for the 20 SOCs (pre-filled from the mock hints; codes are Arsenii's demo set).
- [ ] Tests: fixtures build a valid `CatalogueFile`; unverified row → error; missing OiD file → `shortage` missing. Implement, pass, commit.

### Task 5: Occupations in Demand → shortage
**Files:** `avenir_adapters/occupations_in_demand/parse.py`, test, fixture (five rows of the "Occupations by demand" CSV)
**Interfaces:** `oid_shortage(csv: Path) -> dict[str, Metric]`: 1.0 for levels elevated or critical (verify labels in the file), else 0.0; `region="UK"`, note "UK index; some indicators GB only"; imputed → `confidence="medium"`; `x`/`c`/`z` → missing.
- [ ] Tests, implement, pass, commit.

### Task 6: Routes
**Files:** `data/curated/routes.csv` (`soc2020,nation,kind,name,provider,entry_requirements,url,source,verified_by`), `avenir_etl/build.py` (routes part), test
**Interfaces:** `load_routes(csv) -> RoutesFile`, same validation rules as Task 4. Scotland first (apprenticeships.scot, Graduate Apprenticeships, university course pages), copied by a person, with the page URL; England from Find an Apprenticeship only if time.
- [ ] Tests, implement, pass, commit; open PR "yehor: catalogue, routes, live adapters".

### Cut order if short of time
Wellbeing and stress (leave missing) → OiD shortage → LLM (template only). Never cut: Adzuna with snapshot fallback (pull-the-plug demo), catalogue titles and entry subjects, Scottish routes for the three likely picks.
