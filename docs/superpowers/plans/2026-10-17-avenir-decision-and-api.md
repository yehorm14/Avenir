# Avenir Decision Engine and API Implementation Plan (Nazar)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a student profile plus `snapshots/*.json` into three picks, a hedge, a roadmap and a backtest view, served by a FastAPI app that follows `docs/contracts.md`.

**Architecture:** `packages/decision/avenir_decision/` is pure Python (no I/O, no network, no LLM): ranks, components, picks, hedge, roadmap, reasons, one `recommend()` entry point. `services/api/avenir_api/` is FastAPI: it loads snapshots once at start-up, calls `recommend()`, and wraps every response in the envelope. Live sources (ads, LLM text, tag suggestions) come in through the Protocols in `avenir_contracts.ports`; their real versions are Yehor's work, so you use the safe defaults until his `avenir_adapters.registry` lands.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, pytest, httpx (TestClient), ruff.

**Spec:** `docs/superpowers/specs/2026-10-18-avenir-design.md` (sections 1, 2, 4, 7, 8). Contract in code: `packages/contracts/avenir_contracts/` (read `models.py`, `ports.py`, `snapshots.py`, `envelope.py` first; do not edit them, ask Yehor by PR).

## Global Constraints

- AGENTS.md applies in full. Key rules: no LLM in ranking; every number keeps its `Metric` provenance; missing stays missing (`None`, confidence `low`), never filled; only your folders: `packages/decision/`, `services/api/`, `docker-compose.yml`, `docs/openapi.json`.
- Python ≥ 3.12. No new runtime dependencies beyond `pyproject.toml` without asking Yehor.
- Component scores are 0 to 100 ranks across the loaded occupation set, `None` when inputs are missing.
- Wording shown to users: "worth exploring", "automation exposure (research estimate)". Never "you should", "don't", "will disappear".
- The demo must run with no API keys and with only `snapshots/mock/` present.
- Scoring uses the numbers in `careers.json` only. Live ad counts are overlaid for display after scoring, so the same request always gives the same picks.
- Branches `nazar/decision` and `nazar/api` from `main`; draft PRs with `.github/pull_request_template.md`; context file `context/nazar-backend.md`.
- Run everything from the repo root: `pip install -e ".[dev]"` once, then `pytest`, `ruff check .`.

## Review Focus

1. A first idea typed loosely (`"Architect "`, `"architecture"`, `"ARCHITECT"`) or unknown (`"astronaut"`) → 200 with `first_idea` resolved or `null`, never 500. Test in Task 6.
2. Empty profile (no interests, no qualifications, no text) → 200, every fit 50 with confidence `low`, picks still returned. Test in Task 3.
3. A metric missing for every career (e.g. all `exposure_inhouse` None) → ranks `None` for that input, components fall back to the inputs present, no ZeroDivisionError. Test in Tasks 1 and 4.
4. Zero or one career passes the fit gate → fewer picks, `hedge` may be `null`, explanation says so, no IndexError. Test in Task 5 and Task 13.
5. No snapshots at all (fresh clone where `snapshots/mock/` was deleted) → app still starts, `/health` reports `missing`, `/api/v1/recommendations` returns 503 `UPSTREAM_UNAVAILABLE` in the envelope. Test in Task 12.

## File Structure

```
packages/decision/avenir_decision/
  normalise.py    rank_0_100
  confidence.py   lowest, component_confidence, downgrade
  fit.py          head_start, fit_scores
  components.py   score_components (return, market risk, disruption risk, risk)
  picks.py        choose_picks
  compare.py      vs_first_idea, COMPONENT_NAMES
  first_idea.py   resolve_first_idea
  hedge.py        choose_hedge
  roadmap.py      build_roadmap
  reasons.py      pick_reasons
  recommend.py    recommend  (the one entry point the API calls)
packages/decision/tests/test_<module>.py   one per module, plus conftest.py with fixtures
services/api/avenir_api/
  app.py          create_app, startup snapshot load, CORS
  envelope.py     ok(), fail(), exception handlers, request ids
  deps.py         default ports (registry if importable, else contract defaults)
  routes_read.py  /health, /sources, careers, hedge, backtest, routes
  routes_write.py /profile, /recommendations, /demo/live
  export_openapi.py
services/api/tests/test_*.py
services/api/Dockerfile, docker-compose.yml (repo root), docs/openapi.json
```

---

## Track A: decision package (branch `nazar/decision`)

### Task 1: Ranks

**Files:** Create `packages/decision/avenir_decision/normalise.py`, `packages/decision/tests/conftest.py`, `packages/decision/tests/test_normalise.py`

**Interfaces:**
- Produces: `rank_0_100(values: Mapping[str, float | None], higher_is_better: bool = True) -> dict[str, float | None]`
- Produces (conftest): fixtures `snap` (= `avenir_contracts.mock.build()` loaded into a `Snapshots`, careers keyed by SOC), `careers` (list of 20 `Career`), `profile_amira` (`ProfileIn(interests=["maths","art","design"], qualifications=[Qualification(subject="maths", level="higher"), Qualification(subject="art", level="higher")], automation_worry=0.5)`).

- [ ] **Step 1: Failing tests**
```python
def test_rank_spreads_0_to_100():
    assert rank_0_100({"a": 1, "b": 2, "c": 3}) == {"a": 0.0, "b": 50.0, "c": 100.0}
def test_rank_lower_is_better():
    assert rank_0_100({"a": 1, "b": 3}, higher_is_better=False) == {"a": 100.0, "b": 0.0}
def test_ties_share_average_rank():
    assert rank_0_100({"a": 1, "b": 1, "c": 2}) == {"a": 25.0, "b": 25.0, "c": 100.0}
def test_none_stays_none_and_single_value_is_50():
    assert rank_0_100({"a": None, "b": 5}) == {"a": None, "b": 50.0}
def test_all_missing():
    assert rank_0_100({"a": None, "b": None}) == {"a": None, "b": None}
```
- [ ] **Step 2:** `pytest packages/decision/tests/test_normalise.py` → FAIL (import error).
- [ ] **Step 3:** Implement. Percentile of average rank among non-None values: `(avg_rank_index) / (n - 1) * 100`, rounded to 1 decimal; `n == 1` → 50.0.
- [ ] **Step 4:** Tests pass.
- [ ] **Step 5:** Commit `feat(decision): 0-100 ranks with ties and missing values`.

### Task 2: Confidence

**Files:** `avenir_decision/confidence.py`, `tests/test_confidence.py`

**Interfaces:**
- Produces: `lowest(*levels: Confidence) -> Confidence`; `downgrade(level: Confidence) -> Confidence` (high→medium→low→low); `component_confidence(metrics: Sequence[Metric]) -> Confidence`: lowest confidence among present metrics, then `downgrade` once if any input is missing; all missing → `"low"`.

- [ ] **Step 1: Failing tests**: `lowest("high","medium") == "medium"`; `downgrade("low") == "low"`; two present high + one missing → `"medium"`; all missing → `"low"`.
- [ ] **Steps 2-5:** run (fail), implement with `CONFIDENCE_ORDER` from `avenir_contracts.vocab`, run (pass), commit `feat(decision): confidence rules`.

### Task 3: Fit and head start

**Files:** `avenir_decision/fit.py`, `tests/test_fit.py`

**Interfaces:**
- Consumes: `ProfileIn`, `Career` from `avenir_contracts`.
- Produces: `head_start(profile: ProfileIn, career: Career) -> float` in 0..1; `fit_scores(profile: ProfileIn, careers: Sequence[Career]) -> dict[str, ComponentScore]` keyed by `soc2020`.

Rules (decided here, not in the spec):
- `head_start`: share of `career.entry_subjects` the student holds; a subject at `higher`, `advanced_higher` or `a_level` counts 1.0, at `national5` or `gcse` 0.5 (take the best level per subject). No entry subjects → 1.0.
- `fit = 100 * overlap * (0.8 + 0.2 * head_start)`, rounded to 1 decimal, where `overlap = |P ∩ C| / min(|P|, |C|)`, P = profile interests, C = career interest tags; C empty → overlap 0.
- P empty → every career gets `ComponentScore(score=50.0, confidence="low")`.
- Confidence `high` if `len(P) >= 3`, else `medium`.

- [ ] **Step 1: Failing tests**
```python
def test_amira_fits_architect_better_than_radiographer(profile_amira, careers):
    s = fit_scores(profile_amira, careers)
    arch = next(c for c in careers if c.title == "Architect").soc2020
    rad = next(c for c in careers if c.title == "Radiographer").soc2020
    assert s[arch].score > s[rad].score
def test_empty_profile_is_neutral(careers):
    s = fit_scores(ProfileIn(), careers)
    assert {v.score for v in s.values()} == {50.0} and {v.confidence for v in s.values()} == {"low"}
def test_head_start_counts_national5_as_half(careers):
    arch = next(c for c in careers if c.title == "Architect")   # entry: maths, art, physics
    p = ProfileIn(qualifications=[Qualification(subject="maths", level="national5")])
    assert head_start(p, arch) == pytest.approx(0.5 / 3)
def test_fit_bounded(profile_amira, careers):
    assert all(0 <= v.score <= 100 for v in fit_scores(profile_amira, careers).values())
```
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): fit and head start`.

### Task 4: Return and risk components

**Files:** `avenir_decision/components.py`, `tests/test_components.py`

**Interfaces:**
- Consumes: `rank_0_100`, `component_confidence`, `downgrade`, `fit_scores`.
- Produces: `score_components(profile: ProfileIn, careers: Sequence[Career]) -> dict[str, Components]`; constant `RISK_WEIGHT_RANGE = (0.2, 0.8)`.

Rules (each sub-score is a weighted mean over the inputs that are present, weights renormalised; all inputs missing → `score=None, confidence="low"`):
- `expected_return` = ranks (higher is better) of `pay_now` 0.4, `pay_early` 0.2, `pay_ceiling` 0.2, `pay_growth_10y` 0.2.
- `market_risk` (higher = riskier) = rank of `demand_trend` with `higher_is_better=False` 0.5; shortage 0.25 where flag 1.0 → 0, flag 0.0 → 100; rank of `ads_now` with `higher_is_better=False` 0.25.
- `disruption_risk` = rank of blended exposure, blend = `0.7*exposure_ilo + 0.3*exposure_inhouse` when both present, else whichever is present. If both present and `abs(ilo - inhouse) > 0.2`, `downgrade` the confidence (spec section 4: "confidence widens when they disagree").
- `risk` = `(1-w)*market_risk + w*disruption_risk`, `w = 0.2 + 0.6*profile.automation_worry`; one side missing → the other alone; confidence `lowest` of the two present.
- Confidence of each component: `component_confidence` of its input metrics. `pay_spread`, `wellbeing`, `stress` are display-only: never scored.

- [ ] **Step 1: Failing tests**
```python
def test_slider_moves_risk_toward_disruption(careers):
    lo = score_components(ProfileIn(automation_worry=0.0), careers)
    hi = score_components(ProfileIn(automation_worry=1.0), careers)
    soc = careers[0].soc2020
    c = hi[soc]
    expected = 0.2 * c.market_risk.score + 0.8 * c.disruption_risk.score
    assert c.risk.score == pytest.approx(expected, abs=0.1)
    assert any(lo[s].risk.score != hi[s].risk.score for s in hi)
def test_all_inhouse_missing_falls_back_to_ilo(careers):
    stripped = [c.model_copy(update={"metrics": c.metrics.model_copy(update={
        "exposure_inhouse": Metric.missing("index_0_1", "m2")})}) for c in careers]
    out = score_components(ProfileIn(), stripped)
    assert all(v.disruption_risk.score is not None or c.metrics.exposure_ilo.is_missing
               for c, v in zip(stripped, out.values()))
def test_every_component_present_and_bounded(profile_amira, careers):
    for comps in score_components(profile_amira, careers).values():
        for cs in comps.model_dump().values():
            assert cs["score"] is None or 0 <= cs["score"] <= 100
```
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): return and risk components`.

### Task 5: Picks

**Files:** `avenir_decision/picks.py`, `tests/test_picks.py`

**Interfaces:**
- Produces: `FIT_THRESHOLD = 40.0`; `choose_picks(components: Mapping[str, Components], exclude: Collection[str] = (), fit_threshold: float = FIT_THRESHOLD) -> list[tuple[PickTier, str]]`.

Rules: eligible = `fit.score >= fit_threshold` and `expected_return.score` and `risk.score` not None and SOC not in `exclude` (the first idea is excluded, so picks are alternatives to it). Picks are distinct, chosen in this order: `ambitious` = max return; `safe` = min risk among the rest; `balanced` = max `(return - 50) / max(risk, 10)` among the rest. Ties: higher fit, then lower SOC string. Fewer eligible → fewer picks, same order.

- [ ] **Step 1: Failing tests**: (a) built `Components` dicts where the answers are known by hand, asserting exact `[("ambitious","A"),("safe","B"),("balanced","C")]`; (b) first idea excluded; (c) one eligible → `[("ambitious", soc)]`; (d) none eligible → `[]`.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): ambitious, safe, balanced picks`.

### Task 6: First idea and comparison

**Files:** `avenir_decision/first_idea.py`, `avenir_decision/compare.py`, `tests/test_first_idea.py`, `tests/test_compare.py`

**Interfaces:**
- Produces: `resolve_first_idea(text: str, careers: Sequence[Career]) -> Career | None`; `COMPONENT_NAMES = ("fit","expected_return","market_risk","disruption_risk","risk")`; `vs_first_idea(pick: Components, first: Components | None) -> dict[str, float | None]` (pick minus first, 1 decimal; `None` when either side is None or `first` is None).

Resolution order, on `text.strip().casefold()`: exact SOC code → exact title or alias → title or alias contains the text or the text contains it (prefer the shortest title) → `difflib.get_close_matches(cutoff=0.75)` over titles and aliases → `None`.

- [ ] **Step 1: Failing tests**: `"Architect "`, `"ARCHITECT"`, `"architecture"` (alias) → Architect; `"programmer"` → Software developer; `"0004"` → the career with that SOC; `"astronaut"` → None; `vs_first_idea(x, None)` → all None.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): resolve first idea and compare`.

### Task 7: Hedge

**Files:** `avenir_decision/hedge.py`, `tests/test_hedge.py`

**Interfaces:**
- Consumes: `HedgeCandidate` lists from `Snapshots.hedges`.
- Produces: `choose_hedge(top: Career, candidates: Sequence[HedgeCandidate], components: Mapping[str, Components], careers: Mapping[str, Career]) -> Hedge | None`.

Rule: keep candidates that are in `careers` and whose `risk.score` is lower than the top pick's; choose max `skill_overlap` (tie: lower risk). `risk_delta = candidate risk - top risk` (negative). None qualify → `None`.

- [ ] **Step 1: Failing tests**: safer candidate chosen over a higher-overlap riskier one; unknown SOC skipped; no safer candidate → None.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): hedge career`.

### Task 8: Roadmap

**Files:** `avenir_decision/roadmap.py`, `tests/test_roadmap.py`

**Interfaces:**
- Produces: `build_roadmap(profile: ProfileIn, career: Career, routes: Sequence[Route]) -> Roadmap`.

Rules: use only routes with `route.nation == profile.nation`.
- Step 1 "Subjects": entry subjects the student lacks at Higher level or above → "Take Higher <Subject, Subject>"; none lacking → "Keep <subjects> to Higher or Advanced Higher". Subject names title-cased with `_` → space.
- Step 2 "Route in": first route by kind preference `graduate_apprenticeship`, `degree`, `apprenticeship`, `college`; `detail` = `f"{route.name}: {route.entry_requirements}"`, `route` set. No route for the nation → title "Route in", detail "Routes for this nation are missing from our data.", `route=None`.
- Step 3 "First milestone": with a route → "Check the application deadline and open days on the route's page."; without → "Ask your school's careers adviser about routes into <title>."
- `this_month`: with a route → `f"Read {route.name} at {route.url} and note its entry requirements."`; without → `f"Talk to your careers adviser about {career.title}."`
- Never state a deadline date or grade you did not get from the route data.

- [ ] **Step 1: Failing tests**: Scottish profile gets a Scottish route; English profile with only Scottish routes → missing message and `route is None`; student holding maths at Higher is not told to take maths.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): three-step roadmap`.

### Task 9: Reasons

**Files:** `avenir_decision/reasons.py`, `tests/test_reasons.py`

**Interfaces:**
- Produces: `pick_reasons(tier: PickTier, career: Career, comps: Components) -> list[str]` (2 or 3 sentences).

Templates (fill only from present metrics; skip a sentence whose metric is missing):
- pay: `f"Median pay £{v:,.0f} a year ({source_label}, {year})."` from `pay_now`
- demand: `f"Employment trend {v:+.1f}% a year."` from `demand_trend`
- exposure: `f"Automation exposure (research estimate): {v:.2f} on a 0 to 1 scale, {confidence} confidence."` from `exposure_ilo`
- tier line: ambitious "Highest expected return among careers that fit you."; safe "Lowest overall risk among careers that fit you."; balanced "Best return for the risk among careers that fit you."
`source_label`: `{"ashe_t14": "ONS ASHE", "MOCK": "MOCK DATA"}` else the source id.

- [ ] **Step 1: Failing tests**: every number in the output string appears in the career's metrics; a missing `pay_now` → no pay sentence; mock data says "MOCK DATA".
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): template reasons`.

### Task 10: recommend()

**Files:** `avenir_decision/recommend.py`, `avenir_decision/__init__.py` (export `recommend`, `score_components`, `choose_hedge`, `resolve_first_idea`, `build_roadmap`), `tests/test_recommend.py`

**Interfaces:**
- Consumes: everything above; `Snapshots`; `ExplanationWriter`, `TemplateExplanation` from `avenir_contracts.ports`.
- Produces: `recommend(req: RecommendationRequest, snap: Snapshots, writer: ExplanationWriter | None = None) -> RecommendationOut`.

Flow: components for all careers → resolve first idea → `choose_picks(exclude={first.soc2020})` → build `Pick`s with `vs_first_idea` and `pick_reasons` → hedge for the first pick (`snap.hedges.get(soc, [])`) → roadmap for the first pick (`snap.routes.get(soc, [])`) → `writer.explain(out)` (default `TemplateExplanation()`), and if the writer raises, fall back to `TemplateExplanation`. Raises `ValueError("no careers loaded")` if `snap.careers` is empty.

- [ ] **Step 1: Failing tests**: Amira + "architect" on mock data → `first_idea.title == "Architect"`, 1 to 3 picks, none is Architect, each has 5 `vs_first_idea` keys; same request twice → identical output (determinism); a writer that raises → template text, `ai_written is False`; empty careers → ValueError.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(decision): recommend entry point`.
- [ ] **Step 6:** `pytest packages/decision && ruff check packages/decision`, push, open draft PR "nazar: decision engine".

---

## Track B: API (branch `nazar/api`; Tasks 11 to 12 run in parallel with Track A, Task 13 on needs Track A merged)

### Task 11: App, envelope, errors

**Files:** `services/api/avenir_api/{app.py,envelope.py,deps.py}`, `services/api/tests/conftest.py`, `services/api/tests/test_envelope.py`

**Interfaces:**
- Consumes: `Envelope`, `Meta`, `ErrorBody`, `ErrorCode`, `HTTP_STATUS`, `SourceStatus`, `load_snapshots`, ports defaults.
- Produces: `create_app(snapshots: Snapshots | None = None, ads: AdsSource | None = None, writer: ExplanationWriter | None = None, suggester: TagSuggester | None = None) -> FastAPI`; `ok(data, sources: list[SourceStatus]) -> JSONResponse`; `fail(code: ErrorCode, message: str, details: list[ErrorDetail] = []) -> JSONResponse`. App state: `app.state.snap`, `.ads`, `.writer`, `.suggester`.
- `deps.default_ports()`: `try: from avenir_adapters.registry import ads_source, explanation_writer, tag_suggester` → use them; `except ImportError` → `SnapshotAds()`, `TemplateExplanation()`, `NoTagSuggester()`.
- Exception handlers: `RequestValidationError` → 422 `VALIDATION_ERROR` with one `ErrorDetail(field=".".join(loc), issue=msg)` per error; `HTTPException(404)` → `NOT_FOUND`; any other exception → 500 `INTERNAL` with message "Something went wrong" (log the traceback, never return it).
- `meta.as_of` = today ISO date; `meta.request_id` = `uuid4().hex[:12]`, also sent as header `X-Request-ID`.
- CORS: allow `http://localhost:5173` and `http://127.0.0.1:5173`.

- [ ] **Step 1: Failing tests** with `TestClient(create_app(snapshots=<mock Snapshots>))`: unknown route → 404 envelope `ok: false`, `error.code == "NOT_FOUND"`; `create_app(snapshots=Snapshots())` (empty) starts and `/health` shows every source `missing`.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(api): app, envelope and error handling`.

### Task 12: Read endpoints

**Files:** `services/api/avenir_api/routes_read.py`, `services/api/tests/test_read.py`

**Interfaces:** routes exactly as `docs/contracts.md`; every 200 returns `Envelope[T]` with `meta.sources` = `app.state.snap.statuses` (+ the ads status where ads are shown).
- `GET /health` → `{"status": "ok", "sources": [...]}`
- `GET /api/v1/sources` → `list[SourceStatus]`
- `GET /api/v1/careers/{soc}` → `Career`, with `metrics.ads_now` replaced by `ads.ads_now(career, "UK")[0]`; unknown → 404
- `GET /api/v1/backtest/years` → `list[int]` sorted; `GET /api/v1/backtest?year=Y` → `BacktestYear`; missing year → 404; `year` outside 2010-2020 → 422
- `GET /api/v1/routes/{soc}?nation=scotland` → `list[Route]` for that nation (may be empty); unknown SOC → 404; bad nation → 422

- [ ] **Step 1: Failing tests** for each route: happy path on mock data, 404 and 422 cases, and `meta.sources` non-empty.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(api): read endpoints`. Push, draft PR "nazar: API skeleton".

### Task 13: Write endpoints (after Track A is merged; rebase `nazar/api` on `main`)

**Files:** `services/api/avenir_api/routes_write.py`, `services/api/tests/test_write.py`

**Interfaces:**
- `POST /api/v1/profile` body `ProfileIn` → `ProfileOut`: `suggested_tags = suggester.suggest(free_text)` (an exception → `[]`); `interests` = profile interests then new suggestions, no duplicates; `tag_source = suggester.name` (or `"none"` if it failed).
- `POST /api/v1/recommendations` body `RecommendationRequest` → `RecommendationOut` from `recommend(req, snap, writer)`; then overlay `ads_now` for each pick, the first idea and the hedge career via `ads.ads_now`; add the ads `SourceStatus` to `meta.sources`. `snap.careers` empty → 503 `UPSTREAM_UNAVAILABLE`.
- `GET /api/v1/careers/{soc}/hedge` → `Hedge | None` using `score_components(ProfileIn(), careers)` and `choose_hedge`.
- `POST /api/v1/demo/live` body `{"enabled": bool}` → `{"live": bool}`, calls `ads.set_live(enabled)` (pull the plug).

- [ ] **Step 1: Failing tests**: Amira flow end to end (profile → recommendations) returns picks and `explanation.text`; slider 0 vs 1 can change the order and both are 200; `{"first_idea": ""}` → 422 with `details[0].field` ending in `first_idea`; empty snapshots → 503; `demo/live false` then recommendations → ads status not `live`.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(api): profile, recommendations, hedge, pull the plug`.

### Task 14: OpenAPI export and Docker

**Files:** `services/api/avenir_api/export_openapi.py`, `docs/openapi.json`, `services/api/Dockerfile`, `docker-compose.yml`, `Makefile` (add `run` and `openapi` targets only)

**Interfaces:**
- `python -m avenir_api.export_openapi` writes `docs/openapi.json` (pretty, sorted keys). The frontend generates its TypeScript client from this file; re-run and commit it whenever an endpoint changes.
- `docker compose up` starts `api` on port 8000 (`uvicorn avenir_api.app:app --host 0.0.0.0 --port 8000`, where `app = create_app()` at module level), mounting `./snapshots` read-only. Leave a commented `web:` service for the frontend team.
- `make run` = `uvicorn avenir_api.app:app --reload --port 8000`.

- [ ] **Step 1:** Test: exported schema contains every path in `docs/contracts.md`.
- [ ] **Steps 2-5:** fail, implement, pass, commit `feat(api): openapi export and docker compose`.

### Task 15: Provenance and freeze tests

**Files:** `services/api/tests/test_provenance.py`, `services/api/tests/test_freeze.py`

- [ ] **Step 1:** `test_every_metric_has_provenance`: walk the JSON of `/api/v1/recommendations` (Amira + "architect"); every dict that has a `"unit"` key also has non-empty `source`, `region`, `granularity`, `confidence`.
- [ ] **Step 2:** `test_no_mock_at_freeze`: `pytest.mark.skipif(os.environ.get("AVENIR_FREEZE") != "1")`; with the default snapshot dir, no `SourceStatus.status == "mock"` and no metric `source == "MOCK"`.
- [ ] **Step 3:** Run all: `pytest && ruff check .` → green. Commit `test(api): provenance and freeze checks`. Mark the PR ready, update `context/nazar-backend.md`, tell Yehor.

---

## Self-review notes
- Spec section 4 coverage: fit (T3), return (T4), market risk (T4), disruption risk with disagreement (T4), risk with slider (T4), picks (T5), hedge (T7), comparison (T6), confidence (T2, T4), roadmap (T8). Section 7 endpoints: T12, T13. Section 8 "explanation cites only numbers": template reasons (T9); the LLM validator is Yehor's.
- Not in this plan: backtest computation (Arsenii), ETL and live adapters (Yehor), frontend.
