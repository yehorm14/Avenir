# Frontend handoff: Avenir

For the frontend developers (React + Vite + TypeScript, `apps/web/`). You do not need to know the backend.
Everything below is backed by a file in this folder or by `docs/contracts.md`.

## 1. TL;DR

- **What the app shows:** Amira, 17, picks her interests and types a first career idea. Avenir shows three
  career cards (Ambitious, Safe, Balanced) compared with her first idea, a hedge career, a "how did our past ratings hold up"
  backtest, a roadmap into the career, and a badge on every number saying where it came from.
- **The API is not up yet.** Develop against the JSON in [`examples/`](examples/). They are real payloads built
  from the data the backend loads today (partly sample data: those values have `source: "MOCK"` and `status: "mock"`).
- **Types:** generate them now from [`schemas/`](schemas/) (for example with `json-schema-to-typescript`).
  Once Nazar publishes `docs/openapi.json`, generate from that instead and drop `schemas/`.
- **The example files are regenerated** whenever data changes (section 8). Never edit them by hand.

## 2. Envelope and errors

Every endpoint answers with the same envelope:

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": { "as_of": "...", "request_id": "...", "sources": [{ "name": "...", "status": "live", "quality": null, "as_of": null, "region": "UK" }] }
}
```

On failure `ok` is `false`, `data` is `null` and `error` is `{code, message, details[{field, issue}]}`.
See [`examples/envelope_career_2451.json`](examples/envelope_career_2451.json) (success) and
[`examples/error_404.json`](examples/error_404.json) (failure). Schemas: `schemas/Meta.json`,
`schemas/SourceStatus.json`, `schemas/ErrorBody.json`.

| Code | HTTP | When |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | Bad input, unknown interest id, slider out of range |
| `NOT_FOUND` | 404 | Unknown SOC code or backtest year |
| `UPSTREAM_UNAVAILABLE` | 503 | No careers loaded |
| `INTERNAL` | 500 | Anything else (no traceback returned) |

Serving a snapshot or sample data is **not** an error: you get 200 and that source's status in `meta.sources`.

## 3. Endpoints

`soc` is a four-digit SOC 2020 code, e.g. `2451`. Schemas are in `schemas/<Model>.json`.

| Method and path | Returns | Example file |
| --- | --- | --- |
| `GET /health` | status, `ml_mode` (real, mock, mixed, missing), sources | comes with the API |
| `GET /api/v1/tags` | `Tag[]`: the interest checklist | `examples/tags.json` |
| `GET /api/v1/careers` | `Career[]`: the 20 demo careers | `examples/careers.json` lists their `soc2020` and `title`; one full `Career` is `examples/career_2451.json` |
| `GET /api/v1/careers/{soc}` | `Career` | `examples/career_2451.json`, wrapped: `examples/envelope_career_2451.json` |
| `GET /api/v1/careers/{soc}/history` | `HistoryPoint[]` | `examples/history_2451.json` |
| `GET /api/v1/careers/{soc}/hedge` | `Hedge` or null | comes with the API (the related roles it is built from: `examples/hedge_candidates_2451.json`) |
| `GET /api/v1/routes/{soc}?nation=scotland` | `Route[]` | `examples/routes_2451.json` |
| `GET /api/v1/crises` | `Crisis[]` | `examples/crises.json` |
| `GET /api/v1/backtest/years` | `int[]` base years | `examples/backtest_years.json` |
| `GET /api/v1/backtest?year=2013` | `BacktestOut {window, caveats, status}` | `examples/backtest_2013.json` (the first year in `backtest_years.json`) |
| `GET /api/v1/sources` | `{statuses, registry}` | `examples/sources.json` |
| `POST /api/v1/profile` | `ProfileIn` in, `ProfileOut` out | comes with the API |
| `POST /api/v1/recommendations` | `{profile, first_idea}` in, `RecommendationOut` out | comes with `recommend()` (Nazar's engine); schema now: `schemas/RecommendationOut.json` |
| `POST /api/v1/demo/live` | `{enabled}` in, `{live}` out | comes with the API |

`first_idea` is a SOC code or free text such as `"architect"` (see `schemas/RecommendationRequest.json`).
The `examples/` files hold the `data` part only unless the name starts with `envelope_` or `error_`.

## 4. Metric and how to render it

Every number in the app is a **Metric** (`schemas/Metric.json`). A `Career` has `metrics`, a map of metric key to
Metric; an absent key also means missing. Example: `examples/career_2451.json`.

| Field | Meaning |
| --- | --- |
| `value` | The number, or `null` for missing |
| `low`, `high` | Range around `value`, or `null` |
| `unit` | e.g. `GBP/year`, `count`, `fraction/year` |
| `as_of` | Year or period the figure is for |
| `source` | Key of the source (look it up in `examples/sources.json` under `registry`), or `MOCK` |
| `region` | Coverage, `UK` by default |
| `granularity` | `occupation`, `parent_group`, `major_group` or `estimate` |
| `confidence` | `high`, `medium` or `low` |
| `flags` | Caveats; each one has a sentence in `examples/flags.json` |
| `status` | `final`, `preliminary`, `mock` or `pending` |
| `note`, `extra` | Free text and metric-specific extras |

**Rendering rules** (every number, every card):

| When | Show |
| --- | --- |
| `status: "mock"` | "sample data" label |
| `status: "preliminary"` | "preliminary" tag |
| `value: null` | the word "missing". Never 0, never blank |
| `low` and `high` set | the range, not only `value` |
| `granularity: "major_group"` | "job group" badge. Never present it as occupation-level (`wellbeing` and `stress` are always group-level) |
| Source covers England only (Skills England sector assessments, Find an Apprenticeship) | "England" label |
| Occupations in Demand (the `shortage` metric) | "UK (some indicators GB)" label |
| Each entry in `flags` | the sentence from `examples/flags.json`. Flags with `"must_mention": true` are always visible on the card, not hidden behind a tooltip |
| `confidence` | a high / medium / low badge |
| `source` | "Source: <source name>" plus `as_of` |
| Adzuna numbers (`ads_now`) | "Jobs by Adzuna" |
| `explanation.ai_written` is `true` | "AI-written, check the source" next to the text |

**Wording** (the user is 17): say "worth exploring". Never "you should", "don't" or "AI will take this job". Label
the `exposure` metric "Automation exposure (research estimate)". Exposure is not job loss.

## 5. Live vs snapshot (pull the plug)

Each entry in `meta.sources` has `status`: `live`, `snapshot`, `mock` or `missing`. Show it as a badge
next to the source name. Examples: `examples/sources.json` (`statuses`) and the `meta` in
`examples/envelope_career_2451.json`.

For the demo, `POST /api/v1/demo/live` with `{"enabled": false}` forces snapshot data. Live job adverts (`ads_now`) are
overlaid onto careers, so this switch changes that number and its badge. Build the "pull the plug" button on it.

## 6. Arsenii's ML v1.1 asks (landing tonight or Sunday)

Not in today's examples; build for them now.

- **Job-count lines break at 2021.** Do not join the line across 2021 (flag `recoded_2021`). `examples/history_2451.json` is
  today's `HistoryPoint[]`.
- **History from 2007.** The series gets longer, and pay and job counts will not cover the same years. Treat `null` as
  missing and draw only the lines that have data. Exactly which years have pay: ask Arsenii.
- **Hedge `evidence: "estimate"`** shows an "estimate" badge.
- **"Category level"** (tech slump): show a "category level" badge and read `extra.adverts_category` for the category name.
- **"Sources disagree"**: show a "sources disagree" badge. The exact field arrives with v1.1; ask Arsenii.
- **`young_worker_share`**: optional extra line; show it only when present.
- **`exposure_uk`** is a cross-check on `exposure`, not a second headline number.
- **Text alternative for the timeline**: every chart needs a text version a screen reader can read.

## 7. The cards

Screens, from the project rules (`AGENTS.md`). The ones marked **never cut** stay in the demo, whatever else is dropped.

1. **Three picks vs her first idea** (never cut): Ambitious (highest return among good fits), Safe (lowest risk among
   good fits), Balanced (best return per unit of risk). Each pick has `components` and `vs_first_idea`.
2. **The hedge** (never cut): a related career next to the top pick, with `risk_delta` (negative means safer) (`Hedge`).
3. **Backtest button** (never cut): pick a past year, see how earlier ratings held up. Show bad results as they are.
4. **Roadmap** (never cut): three steps and a "this month" action (`Roadmap`).
5. **Provenance badges** (never cut): section 4.
6. **Pull the plug** (never cut): section 5.

Also: the automation-worry slider (`automation_worry`, 0 to 1, in `ProfileIn`).

## 8. What lands when

| When | What |
| --- | --- |
| Now | Sample data and these examples. Schemas for every model |
| About 01:00 (Sat night) | Nazar's API running on sample data, and `docs/openapi.json`. Point the frontend at it |
| Sunday 08:00 to 10:00 | Real ML data (Arsenii v1.1) and the real career catalogue and routes. Values change, shapes should not |
| Sunday 11:30 | Code freeze |

Examples get regenerated when the data or the contract changes:

```
python -m avenir_contracts.examples
```

Run it from the repo root with the project installed (`pip install -e ".[dev]"`). It rewrites `schemas/` and `examples/`.

## 9. Who to ask

| About | Ask |
| --- | --- |
| Contract and data shapes | Yehor |
| API behaviour | Nazar |
| ML numbers and flags | Arsenii |
