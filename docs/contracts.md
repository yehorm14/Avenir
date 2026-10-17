# API contract v2

**Owner:** Yehor. **Status:** v2, Sat 17 Oct 21:00, built on Arsenii's ML contract.
Sources of truth, in order:
1. `packages/ml/CONTRACTS.md` (Arsenii, v1.0): ML artefacts in `snapshots/ml/`, the `Metric` shape, flags, `MUST_MENTION`, confidence rules, backtest windows.
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

Serving a snapshot or mock is not an error: 200 with that source's status.

## Endpoints

| Method and path | Returns |
| --- | --- |
| `GET /health` | status, `ml_mode` (real, mock, mixed, missing), sources |
| `GET /api/v1/tags` | `Tag[]`: the interest checklist (from ML `fit.json`) |
| `GET /api/v1/careers` | `Career[]`: the 20 demo careers |
| `GET /api/v1/careers/{soc}` | `Career` (live `ads_now` overlaid) |
| `GET /api/v1/careers/{soc}/history` | `HistoryPoint[]` 2011 to 2025 (break job counts at 2021) |
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
- **Career**: `soc2020, title, official_title, aliases[], description, isco08[{code, share}], entry_subjects[], metrics{key: Metric}`; keys = `vocab.ML_METRICS` + `vocab.CATALOGUE_METRICS`.
- **RecommendationOut**: `first_idea, first_idea_components, picks[0..3]{tier, career, components{fit, expected_return, market_risk, disruption_risk, risk}, vs_first_idea, reasons[]}, hedge, roadmap{steps[3], this_month}, notices[], explanation{text, ai_written, cited_numbers}`.
- **Catalogue / routes files** (`catalogue.py`): `snapshots/catalogue.json`, `snapshots/routes.json`, with mocks in `snapshots/mock/`.
