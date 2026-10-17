# API contract v2.1

**Owner:** Yehor. **Status:** v2.1, Sat 17 Oct, built on Arsenii's ML contract v1.1.
Sources of truth, in order:
1. `packages/ml/CONTRACTS.md` v1.1 (Arsenii, landing from him): ML artefacts in `snapshots/ml/`, the `Metric` shape, flags, `MUST_MENTION`, confidence rules, backtest windows.
2. `packages/contracts/avenir_contracts/` (Yehor): API models, the envelope, the catalogue and routes files, the joined loader `load_data()`, and the ports for live adapters.
This page summarises them. Change either only by PR with "needs a contract change" ticked.

## Envelope (every response)
`{ok, data, error: {code, message, details[{field, issue}]} | null, meta: {as_of, request_id, sources[{name, status: live|snapshot|mock|missing, quality, as_of, region}]}}`

| Code | HTTP | When |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | Bad input, unknown interest id, slider out of range |
| `NOT_FOUND` | 404 | Unknown SOC code or backtest year |
| `UPSTREAM_UNAVAILABLE` | 503 | No careers loaded |
| `INTERNAL` | 500 | Anything else (no traceback returned) |

Serving a snapshot or mock is not an error: 200 with that source's status. Error envelopes may have an empty `meta.sources`.
A malformed SOC (not 4 digits) is `VALIDATION_ERROR` 422; a well-formed unknown SOC is `NOT_FOUND` 404.

## Endpoints

| Method and path | Returns |
| --- | --- |
| `GET /health` | status, `ml_mode` (real, mock, mixed, missing), sources |
| `GET /api/v1/tags` | `Tag[]`: the interest checklist (from ML `fit.json`) |
| `GET /api/v1/careers` | `Career[]`: the 20 demo careers |
| `GET /api/v1/careers/{soc}` | `Career` (live `ads_now` overlaid) |
| `GET /api/v1/careers/{soc}/history` | `HistoryPoint[]` 2007 to 2025 (pay only before 2011, job counts from 2011, break at 2021) |
| `GET /api/v1/careers/{soc}/hedge` | `Hedge` or null |
| `GET /api/v1/routes/{soc}?nation=scotland` | `Route[]` |
| `GET /api/v1/crises` | `Crisis[]` |
| `GET /api/v1/backtest/years` | `int[]` base years |
| `GET /api/v1/backtest?year=2013` | `BacktestOut {window, caveats, status}` |
| `GET /api/v1/sources` | `{statuses, registry}` |
| `POST /api/v1/profile` | `ProfileIn` → `ProfileOut {suggested[{tag, score, matched}], tag_source, interests}` |
| `POST /api/v1/recommendations` | `{profile, first_idea}` → `RecommendationOut` |
| `POST /api/v1/demo/live` | `{enabled}` → `{live}` (pull the plug on live ads) |

## Key models
- **Metric** (`metric.py`): ML shape `{value, low, high, unit, as_of, source, granularity, confidence, flags[], status, note, extra}` plus `region` (default UK). `value: null` = missing; the UI says so.
- **Hedge** (and ML `HedgeCandidate`): `for_soc, career, similarity, shared_skills[], why, evidence (title | estimate, optional), risk_delta, status`.
- **Crisis**: `key, label, window, measure, baseline_median, baseline_real_pay_median (optional), status, flags[]`.
- **Career**: `soc2020, title, official_title, aliases[], description, isco08[{code, share}], entry_subjects[], metrics{key: Metric}`; keys = `vocab.ML_METRICS` + `vocab.CATALOGUE_METRICS`.
- **RecommendationOut**: `first_idea, first_idea_candidates[{soc2020, title}] (equal matches of an ambiguous first idea; first_idea is null then), first_idea_components, picks[0..3]{tier, career, components{fit, expected_return, market_risk, disruption_risk, risk}, vs_first_idea, reasons[]}, hedge, roadmap{steps[3], this_month}, notices[], explanation{text, ai_written, cited_numbers}`.
- **Catalogue / routes files** (`catalogue.py`): `snapshots/catalogue.json`, `snapshots/routes.json`, with mocks in `snapshots/mock/`.

## ML v1.1 additions (what the API and UI do)
All additions are backward compatible. The API accepts and passes them through; unknown future fields on ML pass-through shapes are ignored.

| ML v1.1 change | API | UI |
| --- | --- | --- |
| New metric `young_worker_share` (fraction, 2016, includes self-employed) | In `ML_METRICS`; absent or null = missing | Optional card line |
| New flags `category_level`, `bridged_soc2000`, `sources_disagree` | Kept on the metric; all three are `MUST_MENTION`, so their `FLAG_TEXT` sentence goes in `notices` | Show the `FLAG_TEXT` sentence next to the number |
| `exposure_uk` has values | Passed through | Cross-check only; never a second headline |
| `resilience_tech_slump` is real, with `extra.adverts_category` | Passed through | Show the category name and "category level" |
| `resilience_2008` is real, with `extra` parts | Passed through | Show the parts and which one is the headline |
| Hedge `evidence` (`title` or `estimate`) | `evidence` on `Hedge` and `HedgeCandidate` | "estimate" badge when it says `estimate` |
| `history.json` runs 2007 to 2025 | `HistoryPoint[]`; `jobs_k` is null before 2011 | Pay only before 2011, job counts from 2011, break at 2021 |
| Crisis `baseline_real_pay_median` | Optional float on `Crisis` | Optional |
| `schema_version: "1.1"` in every file | Ignored | None |
