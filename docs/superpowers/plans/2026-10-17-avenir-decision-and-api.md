# Avenir Decision Engine and API Implementation Plan (Nazar), v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a student profile plus the loaded data (ML artefacts, catalogue, routes) into three picks against her first idea, a hedge, a roadmap and a track record, served by a FastAPI app with one envelope.

**Architecture:** `avenir_contracts.load_data()` joins Arsenii's ML artefacts (`snapshots/ml/`, via `pathfinder_ml.ML`) with Yehor's catalogue and routes into one `AvenirData` (20 `Career`s with `metrics: dict[str, Metric]`, tags, fit affinities, hedge candidates, history, backtest windows, crises, sources, statuses). `packages/decision/avenir_decision/` is pure Python over `AvenirData` (no I/O, no network, no LLM) with one entry point `recommend()`. `services/api/avenir_api/` is FastAPI: loads data once, calls `recommend()`, wraps every response in the envelope. Live pieces (ads, LLM text, tag suggestions) come through `avenir_contracts.ports`; real versions arrive from Yehor's `avenir_adapters.registry`.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, pytest, httpx, ruff.

**Spec:** `docs/superpowers/specs/2026-10-18-avenir-design.md` (sections 1, 2, 4, 7, 8). Data contract: `packages/ml/CONTRACTS.md` (Arsenii, v1.0: metric keys, flags, confidence, backtest shape). API contract in code: `packages/contracts/avenir_contracts/` (`models.py`, `metric.py`, `data.py`, `ports.py`, `envelope.py`, `vocab.py`). Read all of them first; edit none (ask Yehor in a PR).

## Global Constraints

- AGENTS.md applies in full: no LLM in ranking; every number keeps its `Metric`; missing stays missing; only your folders (`packages/decision/`, `services/api/`, `docker-compose.yml`, `docs/openapi.json`, `context/nazar-backend.md`).
- Python ≥ 3.12; no new runtime dependencies without asking Yehor.
- Component scores are 0 to 100. Fit is absolute (mean affinity × 100 × head start); the other four are ranks across the 20 demo careers, `None` when their inputs are missing.
- Metric keys are exactly `vocab.ML_METRICS` and `vocab.CATALOGUE_METRICS`; a key absent from `career.metrics` is treated as missing.
- Wording: "worth exploring", "GenAI exposure (research estimate)". Never "you should", "don't", "will disappear".
- Any text that shows a number carrying a `MUST_MENTION` flag (`pathfinder_ml.MUST_MENTION`) must come with that flag's sentence (`pathfinder_ml.FLAG_TEXT`); `RecommendationOut.notices` carries them.
- The demo must run with no API keys, on `snapshots/ml/mock/` plus `snapshots/mock/` only.
- Scoring uses loaded data only; live ad counts are overlaid after scoring, for display.
- Branches `nazar/decision` and `nazar/api` from `main`; draft PRs with `.github/pull_request_template.md`; squash merge.
- Setup: `pip install -e ".[dev]"`; then `pytest` and `ruff check .` from the repo root.

## Review Focus

1. First idea typed loosely (`"Architect "`, `"ARCHITECTS"`, `"programmer"`) or unknown (`"astronaut"`) → 200 with `first_idea` resolved or `null`. Test in Task 6.
2. Empty profile (no interests, no qualifications) → 200, every fit 50 with confidence `low`, picks still returned. Test in Task 3.
3. Pending metrics everywhere (`exposure_uk`, `resilience_tech_slump`, `resilience_2008` are null in the mocks) → those inputs are skipped, no ZeroDivisionError. Tests in Tasks 1 and 4.
4. A narrow profile where only 1 or 2 careers pass the fit gate → fewer picks, hedge may be `null`, no IndexError. Tests in Tasks 5 and 13.
5. An interest id not in `GET /api/v1/tags` (e.g. `"juggling"`) → 422 `VALIDATION_ERROR` naming it, not 500. Test in Task 13.

## File Structure

```
packages/decision/avenir_decision/
  normalise.py   rank_0_100
  confidence.py  lowest, downgrade, component_confidence
  fit.py         head_start, fit_scores
  components.py  score_components
  picks.py       FIT_RELATIVE, FIT_FLOOR, eligible, choose_picks
  compare.py     COMPONENT_NAMES, vs_first_idea
  first_idea.py  resolve_first_idea
  hedge.py       choose_hedge
  roadmap.py     build_roadmap
  reasons.py     pick_reasons, notices_for
  recommend.py   recommend
packages/decision/tests/conftest.py + test_<module>.py
services/api/avenir_api/
  app.py, envelope.py, deps.py, routes_read.py, routes_write.py, export_openapi.py
services/api/tests/test_*.py, services/api/Dockerfile, docker-compose.yml, docs/openapi.json
```

---

## Track A: decision package (branch `nazar/decision`)

### Task 1: Ranks

**Files:** `avenir_decision/normalise.py`, `tests/conftest.py`, `tests/test_normalise.py`

**Interfaces:**
- Produces: `rank_0_100(values: Mapping[str, float | None], higher_is_better: bool = True) -> dict[str, float | None]`.
- Produces (conftest): `data` = `load_data(snapshot_dir=tmp)` after `avenir_contracts.mock.write(tmp / "mock")` (20 careers, mock catalogue, Arsenii's ML mocks); `careers` = `list(data.careers.values())`; `amira` = `ProfileIn(interests=["maths","art_drawing","design","building_spaces"], qualifications=[Qualification(subject="maths", level="higher"), Qualification(subject="art", level="higher")], nation="scotland", automation_worry=0.5)`.

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
- [ ] **Step 3:** Implement: average rank index among non-None values, `/(n-1)*100`, 1 decimal; `n == 1` → 50.0.
- [ ] **Step 4:** PASS. **Step 5:** commit `feat(decision): 0-100 ranks with ties and missing values`.

### Task 2: Confidence

**Files:** `avenir_decision/confidence.py`, `tests/test_confidence.py`

**Interfaces:** `lowest(*levels: Confidence) -> Confidence`; `downgrade(level) -> Confidence` (high→medium→low→low); `component_confidence(metrics: Sequence[Metric | None]) -> Confidence`: lowest among present metrics, `downgrade` once if any input is missing (None or `value is None`); all missing → `"low"`.

- [ ] Tests: `lowest("high","medium") == "medium"`; `downgrade("low") == "low"`; two present `high` + one missing → `"medium"`; all missing → `"low"`. Fail, implement with `CONFIDENCE_ORDER`, pass, commit `feat(decision): confidence rules`.

### Task 3: Fit and head start

**Files:** `avenir_decision/fit.py`, `tests/test_fit.py`

**Interfaces:**
- Consumes: `AvenirData.affinity` (`tag -> soc -> 0..1`, from `fit.json`).
- Produces: `head_start(profile: ProfileIn, career: Career) -> float` (0..1); `fit_scores(profile: ProfileIn, careers: Sequence[Career], affinity: Mapping[str, Mapping[str, float]]) -> dict[str, ComponentScore]`.

Rules:
- Base = mean over the profile's interests of `affinity[tag].get(soc, 0.0)` (the same formula as `pathfinder_ml.ML.fit_scores`). Unknown tag → `ValueError` naming it (the API validates before calling).
- `head_start`: share of `career.entry_subjects` held; `higher`, `advanced_higher`, `a_level` count 1.0, `national5`, `gcse` 0.5 (best level per subject); no entry subjects → 1.0.
- `fit = round(100 * base * (0.8 + 0.2 * head_start), 1)`.
- No interests → every career `ComponentScore(score=50.0, confidence="low")`.
- Confidence `high` if 3 or more interests, else `medium`.

- [ ] **Step 1: Failing tests**
```python
def test_amira_fits_architect_best(amira, careers, data):
    s = fit_scores(amira, careers, data.affinity)
    assert max(s, key=lambda k: s[k].score) == "2451"          # Architects
    assert s["2451"].score > s["2254"].score                    # vs Medical radiographers
def test_empty_profile_is_neutral(careers, data):
    s = fit_scores(ProfileIn(), careers, data.affinity)
    assert {v.score for v in s.values()} == {50.0} and {v.confidence for v in s.values()} == {"low"}
def test_unknown_tag_raises(careers, data):
    with pytest.raises(ValueError, match="juggling"):
        fit_scores(ProfileIn(interests=["juggling"]), careers, data.affinity)
def test_head_start_counts_national5_as_half(data):
    arch = data.careers["2451"]                                 # mock entry subjects: maths, art, physics
    p = ProfileIn(qualifications=[Qualification(subject="maths", level="national5")])
    assert head_start(p, arch) == pytest.approx(0.5 / 3)
```
- [ ] Fail, implement, pass, commit `feat(decision): fit and head start`.

### Task 4: Return and risk components

**Files:** `avenir_decision/components.py`, `tests/test_components.py`

**Interfaces:** `score_components(profile: ProfileIn, careers: Sequence[Career], affinity: Mapping[str, Mapping[str, float]]) -> dict[str, Components]`.

Rules. Each component is a weighted mean of the inputs that are present (weights renormalised); all inputs missing → `score=None, confidence="low"`. "rank" = `rank_0_100` across the careers passed in.
- `expected_return` (higher = better): rank `pay_median` 0.5, rank `pay_p90` 0.2, rank `real_pay_change_10y` 0.3.
- `market_risk` (higher = riskier): rank `demand_trend` with `higher_is_better=False` 0.5; resilience 0.35 = rank, `higher_is_better=False`, of the mean of the present `resilience_covid`, `resilience_cost_of_living`, `resilience_tech_slump`, `resilience_2008` values; shortage 0.15 = 0 if `shortage.value == 1` else 100 (skip if missing).
- `disruption_risk`: rank of `exposure`. `downgrade` confidence once if `exposure.high - exposure.low > 0.2` (wide `multi_isco` spread), and once more if `exposure_uk` is present and differs from `exposure` by more than 0.15.
- `risk = (1-w)*market_risk + w*disruption_risk`, `w = 0.2 + 0.6*profile.automation_worry`; one side missing → the other alone; confidence = `lowest` of the two present.
- `fit` from Task 3.
- Display-only, never scored: `pay_p10`, `jobs`, `demand_trend_2011_19`, `wellbeing`, `stress`, `ads_now`.
- Each component's confidence = `component_confidence` of its input metrics (then the downgrades above).

- [ ] **Step 1: Failing tests**
```python
def test_slider_moves_risk_toward_disruption(careers, data):
    lo = score_components(ProfileIn(automation_worry=0.0), careers, data.affinity)
    hi = score_components(ProfileIn(automation_worry=1.0), careers, data.affinity)
    c = hi["2134"]
    assert c.risk.score == pytest.approx(0.2 * c.market_risk.score + 0.8 * c.disruption_risk.score, abs=0.1)
    assert any(lo[s].risk.score != hi[s].risk.score for s in hi)
def test_pending_resilience_is_skipped(careers, data):
    out = score_components(ProfileIn(), careers, data.affinity)    # tech_slump and 2008 are null in mocks
    assert all(v.market_risk.score is not None for v in out.values())
def test_scores_bounded(amira, careers, data):
    for comps in score_components(amira, careers, data.affinity).values():
        for cs in comps.model_dump().values():
            assert cs["score"] is None or 0 <= cs["score"] <= 100
```
- [ ] Fail, implement, pass, commit `feat(decision): return and risk components`.

### Task 5: Picks

**Files:** `avenir_decision/picks.py`, `tests/test_picks.py`

**Interfaces:** `FIT_RELATIVE = 0.5`, `FIT_FLOOR = 5.0`; `eligible(components: Mapping[str, Components], exclude: Collection[str] = ()) -> list[str]`; `choose_picks(components, exclude=()) -> list[tuple[PickTier, str]]`.

Rules (checked on the mock affinities: Amira's profile gives 6 eligible):
- Eligible: not in `exclude` (the first idea), `expected_return.score` and `risk.score` not None, and `fit.score >= max(FIT_FLOOR, FIT_RELATIVE * best_fit)` where `best_fit` is the highest fit among non-excluded careers. With no interests every fit is 50, so all qualify.
- Distinct picks, in this order: `ambitious` = max return; `safe` = min risk among the rest; `balanced` = max `(return - 50) / max(risk, 10)` among the rest. Ties: higher fit, then lower SOC string. Fewer eligible → fewer picks.
- Tell Arsenii these rules in your PR: his backtest groups (`backtest.json`) must use the same ones (his `balanced` group is null until they are fixed).

- [ ] Tests: hand-built `Components` with known answers → exact `[("ambitious","A"),("safe","B"),("balanced","C")]`; first idea excluded; relative gate (best fit 60 → a career at 29 is out, 30 is in); one eligible → one pick; none → `[]`. Fail, implement, pass, commit `feat(decision): ambitious, safe, balanced picks`.

### Task 6: First idea and comparison

**Files:** `avenir_decision/first_idea.py`, `avenir_decision/compare.py`, tests

**Interfaces:** `resolve_first_idea(text: str, careers: Sequence[Career]) -> Career | None`; `COMPONENT_NAMES = ("fit","expected_return","market_risk","disruption_risk","risk")`; `vs_first_idea(pick: Components, first: Components | None) -> dict[str, float | None]` (pick minus first, 1 decimal; None where either side is None).

Resolution on `text.strip().casefold()` over `title`, `official_title` and `aliases`: exact SOC code → exact name → name contains text or text contains name (prefer the shortest name) → `difflib.get_close_matches(cutoff=0.75)` → `None`.

- [ ] Tests: `"Architect "`, `"ARCHITECTS"`, `"architecture"` → 2451; `"programmer"` → 2134; `"2254"` → 2254; `"astronaut"` → None; `vs_first_idea(x, None)` → all None. Fail, implement, pass, commit `feat(decision): resolve first idea and compare`.

### Task 7: Hedge

**Files:** `avenir_decision/hedge.py`, tests

**Interfaces:** `choose_hedge(top: Career, candidates: Sequence[HedgeCandidate], components: Mapping[str, Components], careers: Mapping[str, Career]) -> Hedge | None`.

Rule (CONTRACTS.md 4.3: "highest similarity among candidates with lower risk"): keep candidates in `careers` with `risk.score` lower than the top pick's; choose max `similarity` (tie: lower risk). `Hedge(for_soc=top.soc2020, career=..., similarity, shared_skills, why, risk_delta=cand_risk - top_risk, status=cand.status)`. None qualify → `None`.

- [ ] Tests: safer lower-similarity candidate beats a riskier higher one; unknown SOC skipped; none safer → None. Fail, implement, pass, commit `feat(decision): hedge career`.

### Task 8: Roadmap

**Files:** `avenir_decision/roadmap.py`, tests

**Interfaces:** `build_roadmap(profile: ProfileIn, career: Career, routes: Sequence[Route]) -> Roadmap`.

Rules (only routes with `route.nation == profile.nation`):
- Step 1 "Subjects": entry subjects not held at Higher or above → `"Take Higher <Subject, Subject>"`; none missing → `"Keep <subjects> to Higher or Advanced Higher"`; subject names title-cased, `_` → space. No entry subjects → "Check the subjects on the route's page."
- Step 2 "Route in": first route by kind preference `graduate_apprenticeship`, `degree`, `apprenticeship`, `college`; `detail = f"{route.name}: {route.entry_requirements}"`. None for the nation → detail "Routes for this nation are missing from our data.", `route=None`.
- Step 3 "First milestone": with a route "Check the application deadline and open days on the route's page."; without, `f"Ask your school's careers adviser about routes into {career.title}."`
- `this_month`: with a route `f"Read {route.name} at {route.url} and note its entry requirements."`; without `f"Talk to your careers adviser about {career.title}."`
- Never state a date or grade that isn't in the route data.

- [ ] Tests: Scottish profile gets a Scottish route; English profile with only Scottish routes → missing message, `route is None`; maths held at Higher is not listed. Fail, implement, pass, commit `feat(decision): three-step roadmap`.

### Task 9: Reasons and notices

**Files:** `avenir_decision/reasons.py`, tests

**Interfaces:** `SOURCE_LABELS = {"ons_ashe_t14": "ONS ASHE", "ilo_wp140": "ILO", "MOCK": "sample data"}`; `pick_reasons(tier: PickTier, career: Career, comps: Components) -> list[str]`; `notices_for(careers: Sequence[Career]) -> list[str]`.

Templates (skip a sentence whose metric is missing):
- tier line: ambitious "Highest expected return among careers that fit you."; safe "Lowest overall risk among careers that fit you."; balanced "Best return for the risk among careers that fit you."
- `pay_median`: `f"Median pay £{v:,.0f} a year for full-time employees ({label}, {as_of})."`
- `demand_trend`: `f"Jobs trend {v*100:+.1f}% a year ({as_of})."`
- `exposure`: `f"GenAI exposure (research estimate): {v:.2f} on a 0 to 1 scale, {confidence} confidence."`
- `notices_for`: for every metric of the given careers, every flag in `pathfinder_ml.MUST_MENTION` → `pathfinder_ml.FLAG_TEXT[flag]`, unique, in first-seen order.

- [ ] Tests: every number in the reasons appears in the career's metrics (after the stated formatting); missing `pay_median` → no pay sentence; a career with `bridged_soc2010` on any metric → its FLAG_TEXT in `notices_for`. Fail, implement, pass, commit `feat(decision): reasons and notices`.

### Task 10: recommend()

**Files:** `avenir_decision/recommend.py`, `avenir_decision/__init__.py` (export `recommend`, `score_components`, `choose_hedge`, `resolve_first_idea`, `build_roadmap`, `fit_scores`), tests

**Interfaces:** `recommend(req: RecommendationRequest, data: AvenirData, writer: ExplanationWriter | None = None) -> RecommendationOut`.

Flow: `score_components` over `data.careers` → `resolve_first_idea` → `choose_picks(exclude={first.soc2020} if first else ())` → `Pick`s with `vs_first_idea` and `pick_reasons` → hedge for the first pick from `data.hedges.get(soc, [])` → roadmap for the first pick from `data.routes.get(soc, [])` → `notices = notices_for(picks + first idea + hedge careers)` → `writer.explain(out)` (default `TemplateExplanation()`; if it raises, use `TemplateExplanation`). `ValueError("no careers loaded")` if `data.careers` is empty.

- [ ] Tests: Amira + "architect" → `first_idea.soc2020 == "2451"`, 1 to 3 picks, none is 2451, 5 keys in each `vs_first_idea`, `notices` non-empty (mocks carry `bridged_soc2010`); same request twice → identical; a writer that raises → template, `ai_written is False`; empty data → ValueError. Fail, implement, pass, commit `feat(decision): recommend entry point`.
- [ ] `pytest packages/decision && ruff check packages/decision`; push; draft PR "nazar: decision engine".

---

## Track B: API (branch `nazar/api`; Tasks 11-12 in parallel with Track A; Task 13 on after Track A is merged)

### Task 11: App, envelope, errors

**Files:** `services/api/avenir_api/{app.py,envelope.py,deps.py}`, `services/api/tests/conftest.py`, `test_envelope.py`

**Interfaces:**
- `create_app(data: AvenirData | None = None, ads: AdsSource | None = None, writer: ExplanationWriter | None = None, suggester: TagSuggester | None = None) -> FastAPI`; `data` defaults to `load_data()`; state on `app.state.data/.ads/.writer/.suggester`; module-level `app = create_app()` only in `app.py`'s `if`-free bottom line used by uvicorn (tests build their own).
- `ok(data, sources: list[SourceStatus]) -> JSONResponse`; `fail(code: ErrorCode, message: str, details: list[ErrorDetail] | None = None) -> JSONResponse`.
- `deps.default_ports()`: `try: from avenir_adapters.registry import ads_source, explanation_writer, tag_suggester` → use them; `except ImportError` → `SnapshotAds()`, `TemplateExplanation()`, `KeywordSuggester()`.
- Handlers: `RequestValidationError` → 422 `VALIDATION_ERROR`, one `ErrorDetail(field=".".join(map(str, loc)), issue=msg)` per error; 404 → `NOT_FOUND`; anything else → 500 `INTERNAL`, message "Something went wrong" (log the traceback, never return it).
- `meta.as_of` = today; `meta.request_id = uuid4().hex[:12]`, also header `X-Request-ID`; `meta.sources` = `data.statuses` (+ adzuna status when ads are shown).
- CORS: `http://localhost:5173`, `http://127.0.0.1:5173`.

- [ ] Tests: unknown route → 404 envelope `ok: false`, `error.code == "NOT_FOUND"`; `create_app(data=AvenirData())` starts and `/health` reports `ml_mode == "missing"`. Fail, implement, pass, commit `feat(api): app, envelope and error handling`.

### Task 12: Read endpoints

**Files:** `services/api/avenir_api/routes_read.py`, `tests/test_read.py`

All return `Envelope[T]`:
- `GET /health` → `{"status": "ok", "ml_mode": data.ml_mode, "sources": [...]}`
- `GET /api/v1/tags` → `list[Tag]` (the checklist)
- `GET /api/v1/sources` → `{"statuses": list[SourceStatus], "registry": dict[str, SourceInfo]}`
- `GET /api/v1/careers` → `list[Career]` (demo set, for the first-idea picker)
- `GET /api/v1/careers/{soc}` → `Career` with `metrics["ads_now"]` replaced by `ads.ads_now(career, "UK")[0]`; unknown → 404
- `GET /api/v1/careers/{soc}/history` → `list[HistoryPoint]`; unknown → 404
- `GET /api/v1/crises` → `list[Crisis]`
- `GET /api/v1/backtest/years` → sorted `list[int]`; `GET /api/v1/backtest?year=Y` → `BacktestOut(window, caveats=data.backtest_caveats, status=data.backtest_status)`; no `year` → latest; unknown year → 404
- `GET /api/v1/routes/{soc}?nation=scotland` → `list[Route]` for that nation (may be empty); unknown SOC → 404; bad nation → 422

- [ ] Tests per route: happy path on mock data, 404 and 422 cases, non-empty `meta.sources`. Fail, implement, pass, commit `feat(api): read endpoints`. Push; draft PR "nazar: API skeleton".

### Task 13: Write endpoints (after Track A is merged; rebase first)

**Files:** `services/api/avenir_api/routes_write.py`, `tests/test_write.py`

- `POST /api/v1/profile` body `ProfileIn` → `ProfileOut`: unknown interest ids → 422 naming them; `suggested = suggester.suggest(free_text)` (exception → `[]`, `tag_source="none"`); `interests` = profile interests, then suggested tags not already there.
- `POST /api/v1/recommendations` body `RecommendationRequest` → `RecommendationOut` from `recommend(req, data, writer)`; unknown interest ids → 422; no careers → 503 `UPSTREAM_UNAVAILABLE`; then overlay `ads_now` on every pick, the first idea and the hedge career via `ads.ads_now`, and add the adzuna `SourceStatus` to `meta.sources`.
- `GET /api/v1/careers/{soc}/hedge` → `Hedge | None` using `score_components(ProfileIn(), ...)` and `choose_hedge`.
- `POST /api/v1/demo/live` body `{"enabled": bool}` → `{"live": bool}`; calls `ads.set_live(enabled)` (pull the plug).

- [ ] Tests: Amira flow (profile → recommendations) returns picks, notices and `explanation.text`; slider 0 and 1 both 200; `{"interests": ["juggling"]}` → 422 with "juggling" in `details`; `{"first_idea": ""}` → 422 with field ending `first_idea`; empty data → 503; `demo/live false` → adzuna status not `live`. Fail, implement, pass, commit `feat(api): profile, recommendations, hedge, pull the plug`.

### Task 14: OpenAPI export and Docker

**Files:** `services/api/avenir_api/export_openapi.py`, `docs/openapi.json`, `services/api/Dockerfile`, `docker-compose.yml`, `Makefile` (add `run` and `openapi` targets only)

- `python -m avenir_api.export_openapi` writes `docs/openapi.json` (indent 2, sorted keys). The frontend generates its client from it; re-export whenever an endpoint changes.
- `docker compose up` starts `api` on 8000 (`uvicorn avenir_api.app:app --host 0.0.0.0 --port 8000`) mounting `./snapshots` read-only; a commented `web:` service for the frontend.
- `make run` = `uvicorn avenir_api.app:app --reload --port 8000`.

- [ ] Test: the exported schema contains every path in Tasks 12 and 13. Fail, implement, pass, commit `feat(api): openapi export and docker compose`.

### Task 15: Provenance and freeze tests

**Files:** `services/api/tests/test_provenance.py`, `services/api/tests/test_freeze.py`

- [ ] `test_every_metric_has_provenance`: walk the JSON of `/api/v1/recommendations` (Amira + "architect"); every dict with a `"unit"` key has non-empty `source`, `confidence`, `status`, and a `flags` list.
- [ ] `test_no_mock_at_freeze` (skip unless `AVENIR_FREEZE=1`): with default data, no `SourceStatus.status == "mock"` for `catalogue`, `routes`, `ml_occupations`, `ml_backtest`, and no metric in a recommendation `is_mock`.
- [ ] `pytest && ruff check .` green. Commit `test(api): provenance and freeze checks`. Mark PR ready; update `context/nazar-backend.md`; tell Yehor.

---

## Handoffs
- **Arsenii:** the pick rules in Task 5 are the ones his backtest groups should use; ask him for public `ML.affinity()` and `ML.backtest_years()` (we read `ml._load(...)` until then, in `avenir_contracts/data.py`, not in your code).
- **Yehor:** `avenir_adapters.registry` (keyword/LLM suggester, Adzuna, LLM explanation) is picked up automatically by `deps.default_ports()`.
- **Frontend:** `docs/openapi.json` after Task 14; the API on `:8000` from the 01:00 checkpoint.

## Self-review notes
- Spec 4 coverage: fit (T3), return (T4), market and disruption risk (T4), slider (T4), picks (T5), hedge (T7), comparison (T6), confidence (T2, T4), roadmap (T8). Spec 7 endpoints: T12, T13 (plus tags, history, crises, careers list for the ML contract's extra artefacts). Spec 8 explanation citing numbers: T9 templates plus `notices`; the LLM number check is Yehor's.
- Changed from the spec on purpose (per `packages/ml/CONTRACTS.md` section 6): no `pay_early`; ceiling is `pay_p90`; no in-house exposure number shown; resilience added to market risk.
