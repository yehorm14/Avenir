# Avenir Data ETL and Live Adapters Implementation Plan (Yehor)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the real `snapshots/careers.json` and `snapshots/routes.json` from downloaded UK data, and provide the live adapters (tag suggester, Adzuna ads, LLM explanation) that Nazar's API plugs in through `avenir_contracts.ports`.

**Architecture:** `packages/adapters/avenir_adapters/` has one module per source: static parsers that read `data/raw/` or `data/curated/` and return `Metric`s, and live adapters implementing the port Protocols. `avenir_adapters.registry` exposes `ads_source()`, `explanation_writer()`, `tag_suggester()` for the API. `packages/etl/avenir_etl/build.py` merges parsers plus Arsenii's artefacts (`demand.json`, `exposure.json` as `MetricFile`) into `careers.json`, validated by `CareersFile`.

**Tech Stack:** Python 3.12, pandas, openpyxl, xlrd, requests, Pydantic v2, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-avenir-design.md` sections 3, 6, 8; `docs/data-sources.md`; `data/manifest.yaml`; contract code in `packages/contracts/avenir_contracts/`.

## Global Constraints

- AGENTS.md applies. Never invent a value or code: a value that cannot be parsed becomes `Metric.missing(...)` with a `note` saying why.
- Units per `avenir_contracts.models.METRIC_UNITS`. Sources are `data/manifest.yaml` ids (`ashe_t14`, `oid_2025`, `ilo_genai_2025`, `adzuna`) or ML artefact names (`m4_demand`, `m2_exposure`).
- Live adapters: 3 s timeout, 1 retry, never raise to the caller, snapshot fallback with status `snapshot`.
- LLM text may cite only numbers already present in the response; otherwise fall back to the template.
- Only my folders: `packages/adapters/`, `packages/etl/`, `packages/contracts/`, `scripts/fetch/`, `data/`.
- Parser tests run on small fixtures committed in `packages/etl/tests/fixtures/` (a few rows copied from the real file), never on `data/raw/`.

## Review Focus

1. ASHE cells with `x`, `..`, `:` or a CV flag (suppressed or unreliable) → missing or low confidence, never 0. Test in Task 4.
2. A career mapped to several ISCO codes → ILO exposure is the mean with granularity `estimate`. Test in Task 6.
3. Adzuna down, slow or out of quota during the demo → snapshot value within 3 s, status `snapshot`. Test in Task 2.
4. LLM text with a number not in the response (e.g. "£45,000" when pay is £44,800) → rejected, template used. Test in Task 3.
5. A curated row without `verified_by` → build fails loudly, naming the row. Test in Task 7.

---

### Task 1: Registry and keyword tag suggester
**Files:** `avenir_adapters/registry.py`, `avenir_adapters/tags/keyword.py`, `packages/etl/tests/test_tags.py`
**Interfaces:** Produces `tag_suggester() -> TagSuggester`, `ads_source() -> AdsSource`, `explanation_writer() -> ExplanationWriter` (each returns a singleton); `KeywordSuggester.name == "keyword"`, `suggest(text) -> list[InterestTag]` from a word map (e.g. drawing, painting → art; code, computer, games → computers; build, houses → building; fix, repair → fixing_things; numbers, puzzles → maths), max 5 tags, order of first appearance. If Arsenii's matcher model folder exists, `tag_suggester()` returns his suggester instead (name `matcher`).
- [ ] Tests: "I like drawing and fixing things" → `["art", "fixing_things"]`; empty text → `[]`. Implement, pass, commit.

### Task 2: Adzuna live ads
**Files:** `avenir_adapters/adzuna/source.py`, `packages/etl/tests/test_adzuna.py`
**Interfaces:** `AdzunaAds(app_id: str | None, app_key: str | None, snapshot_dir: Path)` implements `AdsSource`. Live only when keys exist and `set_live(True)` (default live if keys exist). Query `what` = first alias or title; 3 s timeout, 1 retry; in-memory cache 10 minutes per SOC. Fallback order: latest `snapshots/adzuna/*.json` entry for that title → `career.metrics.ads_now`. Metric: `unit="count"`, `source="adzuna"`, `granularity="estimate"` (keyword search, not SOC-coded), confidence `medium`, note "Jobs by Adzuna".
- [ ] Tests with `requests` monkeypatched: timeout → snapshot status within the deadline; `set_live(False)` never calls the network; success → status `live`. Implement, pass, commit.

### Task 3: LLM explanation with number check
**Files:** `avenir_adapters/llm/writer.py`, `packages/etl/tests/test_llm.py`
**Interfaces:** `LlmExplanation(base_url, api_key, model)` implements `ExplanationWriter` against an OpenAI-compatible `/chat/completions` (env `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_ENABLED`). `allowed_numbers(rec: RecommendationOut) -> set[str]`; `numbers_in(text) -> set[str]`; any number in the text not in the allowed set → template. Prompt: plain English for a 17-year-old, under 120 words, "worth exploring", no advice verbs. Output `ai_written=True`, `cited_numbers` filled.
- [ ] Tests: invented number rejected; allowed numbers pass; `LLM_ENABLED=false` → template without a network call. Implement, pass, commit.

### Task 4: ASHE pay parser
**Files:** `avenir_adapters/ashe/parse.py`, `packages/etl/tests/test_ashe.py`, fixtures
**Interfaces:** `ashe_pay(ed_dir: Path, year: int) -> dict[str, dict[str, Metric]]` (SOC → `pay_now`, `pay_ceiling`, `pay_spread`); `ashe_age_band(...)` → `pay_early`; `real_growth(now, then, cpih_now, cpih_then) -> float`. Step 1: open the 2025 file (annual pay gross, all employees, table 14.7a, verify), copy five rows to a fixture. Read code, median, p10, p75, p90, n; CV flags → confidence (no flag high, `*` medium, `**`/`x` low or missing). CPIH (ONS series L522, add to manifest) for ten-year real growth; if CPIH is not downloaded, `pay_growth_10y` is missing with note "CPIH not loaded".
- [ ] Tests on fixtures: suppressed → missing; a known row → exact median. Implement, pass, commit.

### Task 5: Occupations in Demand parser
**Files:** `avenir_adapters/occupations_in_demand/parse.py`, test, fixture
**Interfaces:** `oid_shortage(csv: Path) -> dict[str, Metric]`: flag 1.0 for levels elevated or critical (verify labels), 0.0 otherwise; region "UK" with note "some indicators GB"; imputed → confidence `medium`; `x`/`c`/`z` → missing.
- [ ] Tests, implement, pass, commit.

### Task 6: ILO exposure from curated table
**Files:** `avenir_adapters/ilo_exposure/parse.py`, `data/curated/ilo_exposure.csv` (columns `isco08,title,mean,sd,gradient,verified_by`), test
**Interfaces:** `ilo_exposure(csv: Path, isco_codes: list[str]) -> Metric`: one code → that mean, granularity `occupation`; several → mean of means, granularity `estimate`; none found → missing. `low/high` = mean ∓ sd.
- [ ] Tests, implement, pass, commit.

### Task 7: Build careers.json and routes.json
**Files:** `packages/etl/avenir_etl/build.py`, `avenir_etl/curated.py`, `packages/etl/tests/test_build.py`
**Interfaces:** `load_occupations(csv) -> list[CuratedOccupation]` (fails on empty `verified_by` or `soc2020`, naming the row); `build(raw: Path, curated: Path, artefacts: Path) -> CareersFile`; CLI `python -m avenir_etl.build` writes `snapshots/careers.json` and `snapshots/routes.json` (from `data/curated/routes.csv`). Merges: ASHE (T4), OiD (T5), ILO (T6), Adzuna snapshot (`ads_now`), `snapshots/demand.json` → `demand_trend`, `snapshots/exposure.json` → `exposure_inhouse`; anything absent → `Metric.missing`. Interest tags and entry subjects come from the curated CSV.
- [ ] Tests: build on fixtures produces a valid `CareersFile`; a missing artefact → missing metrics, not a crash; unverified row → error. Implement, pass, commit; open PR "yehor: ETL and live adapters".

## Handoffs
- Nazar: `avenir_adapters.registry` (Tasks 1 to 3) as soon as it lands; the API picks it up automatically.
- Arsenii: `demand.json`, `exposure.json` as `MetricFile`; `hedge.json` as `HedgeFile`; `backtest.json` as `BacktestFile`, all in `snapshots/`.
- Team: `data/curated/occupations.csv` codes and `routes.csv` with `verified_by`.
