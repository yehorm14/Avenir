# Frontend handoff: Avenir

For the frontend developers (React + Vite + TypeScript, `apps/web/`). You do not need to know the backend.
Everything below is backed by a file in this folder, `docs/contracts.md`, `AGENTS.md` (team rules) or the ML contract
(`packages/ml/CONTRACTS.md`, Arsenii).

## 1. TL;DR

- **What the app shows:** Amira, 17, picks her interests and types a first career idea. Avenir shows three
  career cards (Ambitious, Safe, Balanced) compared with her first idea, a hedge career, a "how did our past ratings hold up"
  backtest, a roadmap into the career, and a badge on every number saying where it came from.
- **The API is on `main`.** Run it (section 8) and develop against it. The JSON in [`examples/`](examples/) are offline
  fixtures of the same shapes. Today part of the data is sample data: those values have `source: "MOCK"` and `status: "mock"`.
- **Types:** `docs/openapi.json` is published. Generate from it:
  `npx openapi-typescript@7.4.4 docs/openapi.json -o src/api.d.ts`. This output passes `tsc --strict`. `data` and `error`
  are optional in the generated types and `ok` is a plain boolean, so the client must check `ok` before it reads `data`.
  [`schemas/`](schemas/) stays only as a secondary, offline reference.
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

Two notes from `docs/contracts.md`:

- Error envelopes may have an empty `meta.sources` (`[]`). Do not rely on it being filled when `ok` is `false`.
- A malformed SOC (for example `abc` or `245`) is `VALIDATION_ERROR` (422). A well-formed SOC that is unknown (for example
  `9999`) is `NOT_FOUND` (404).

## 3. Endpoints

`soc` is a four-digit SOC 2020 code, e.g. `2451`. Schemas are in `schemas/<Model>.json`.

| Method and path | Returns | Example file |
| --- | --- | --- |
| `GET /health` | status, `ml_mode` (real, mock, mixed, missing), sources | comes with the API |
| `GET /api/v1/tags` | `Tag[]`: the interest checklist. Sample list today (`ml_fit` is `mock`) | `examples/tags.json` |
| `GET /api/v1/careers` | `Career[]`: the 20 demo careers | `examples/careers.json` lists their `soc2020` and `title`; one full `Career` is `examples/career_2451.json` |
| `GET /api/v1/careers/{soc}` | `Career` | `examples/career_2451.json`, wrapped: `examples/envelope_career_2451.json` |
| `GET /api/v1/careers/{soc}/history` | `HistoryPoint[]` | `examples/history_2451.json` |
| `GET /api/v1/careers/{soc}/hedge` | `Hedge` or null (null for 4 of 20 careers today) | comes with the API (the related roles it is built from: `examples/hedge_candidates_2451.json`) |
| `GET /api/v1/routes/{soc}?nation=scotland` | `Route[]` (`[]` for other nations today) | `examples/routes_2451.json` |
| `GET /api/v1/crises` | `Crisis[]` | `examples/crises.json` |
| `GET /api/v1/backtest/years` | `int[]` base years | `examples/backtest_years.json` |
| `GET /api/v1/backtest?year=2013` | `BacktestOut {window, caveats, status}` | `examples/backtest_2013.json` (the first year in `backtest_years.json`) |
| `GET /api/v1/sources` | `{statuses, registry}` | `examples/sources.json` |
| `POST /api/v1/profile` | `ProfileIn` in, `ProfileOut` out | comes with the API |
| `POST /api/v1/recommendations` | `{profile, first_idea}` in, `RecommendationOut` out | comes with `recommend()` (Nazar's engine); schema now: `schemas/RecommendationOut.json`. `first_idea_candidates` (`{soc2020, title}[]`) lists careers an ambiguous typed first idea matches equally; `first_idea` is `null` then (see section 7) |
| `POST /api/v1/demo/live` | `{enabled}` in, `{live}` out | comes with the API |

`first_idea` is a SOC code or free text such as `"architect"` (see `schemas/RecommendationRequest.json`).
The `examples/` files hold the `data` part only unless the name starts with `envelope_` or `error_`.

**Empty lists and null.** Handle these as "nothing to show". The UI shows a plain message, never an error.

- `GET /routes/{soc}` returns `[]` when there are no routes for that nation. Today only `scotland` has routes.
- `GET /careers/{soc}/hedge` returns `data: null` for some careers (4 of 20 today). The message is "no safer related career
  found".
- Today hedges are sample data (`status: "mock"`, source `ml_hedges`) and `evidence` is `null`. Both become real with Arsenii's
  Sunday PR.

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
| `status: "mock"`, or `source: "MOCK"` | "sample data" label |
| `status: "preliminary"` | "preliminary" tag |
| `status: "pending"` | "not available yet" (`value` is `null`) |
| `value: null` | the word "missing". Never 0, never blank |
| The key is absent from `Career.metrics` | "missing" |
| `suppressed` in `flags` | "missing" |
| `low` and `high` set | the range, not only `value` |
| `granularity: "major_group"` | "job group" badge. Never present it as occupation-level (`wellbeing` and `stress` are always group-level) |
| `confidence` | a high / medium / low badge |
| `source` | "Source: <source name>" (look the key up in `examples/sources.json`) plus `as_of` |
| Adzuna numbers (`ads_now`) | "Jobs by Adzuna" |
| `explanation.ai_written` is `true` | "AI-written, check the source" next to the text |
| Each entry in `flags` | the sentence from `examples/flags.json`. Flags with `"must_mention": true` are always visible on the card, not hidden behind a tooltip |

**Flag rules** (from the ML contract, section 2.3). The sentence is always shown; the extra rule is how to draw it:

| Flag | Also |
| --- | --- |
| `recoded_2021` | **Break the job-count line at 2021**: two separate segments, never one line across 2021 |
| `bridged_soc2010`, `bridged_soc2000` | Dashed line or marker for the years it covers |
| `covid_year` | Marker on 2020 |
| `provisional` | Small "provisional" tag |
| `employees_only` | Footnote on the card |
| `imputed_parent` | "estimated" tag |
| `cv_high` | Lower confidence badge (already reflected in `confidence`) |
| `multi_isco` | Show the range |
| `category_level` | Name the category, from `extra.adverts_category` (on `resilience_tech_slump`) |
| `sources_disagree` | "Sources disagree" note, and show the (wider) range (on `exposure`) |
| `pending_source` | "not available yet" |
| `mock` | "sample data" |

**Coverage labels.** Two fields carry coverage: `Metric.region` (default `"UK"`) and `Route.nation`
(`scotland`, `england`, `wales`, `northern_ireland`).

- Show `Route.nation` on every route. England-only sources (Skills England sector assessments, Find an
  Apprenticeship) get an "England" label.
- Show `Metric.region` when it is not `"UK"`.
- The `shortage` metric (Occupations in Demand) always gets the label "UK (some indicators GB)", keyed on the metric key,
  because its `region` will say `UK`.
- **Not yet demonstrated:** no example in `examples/` has a `Metric.region` other than `UK`, so the set of values is not
  yet shown. Ask Yehor before hard-coding a list.

**Wording** (the user is 17): say "worth exploring". Never "you should", "don't" or "AI will take this job". Label
the `exposure` metric "Automation exposure (research estimate)". Exposure is not job loss.

## 5. Live vs snapshot (pull the plug)

Each entry in `meta.sources` has `status`: `live`, `snapshot`, `mock` or `missing`. Show it as a badge
next to the source name. Examples: `examples/sources.json` (`statuses`) and the `meta` in
`examples/envelope_career_2451.json`.

For the demo, `POST /api/v1/demo/live` with `{"enabled": false}` forces snapshot data. Live job adverts (`ads_now`) are
overlaid onto careers. Build the "pull the plug" button on this call.

Today `ads_now` and the `adzuna` entry in `meta.sources` are `mock` (a sample number from the sample catalogue). They become
`missing` once the real catalogue is built on Sunday, unless someone has Adzuna keys. So today `/demo/live` changes nothing
visible: the call returns `{live}` and the page must not break. What the button should switch off (Adzuna, the LLM, the
matcher) is still an open decision (plan, section 7).

## 6. ML contract v1.1 (Arsenii): what changes for the UI

Source: ML CONTRACTS v1.1 (Arsenii; `git -C C:/dev/KATYATA show 03fb482:packages/ml/CONTRACTS.md`; it lands on main when he
pushes). All changes are additions, so build for them now. Today's examples are still v1.0 data, and `flags.json` has only the
v1.0 flags until then; the three new flags are in the table in section 4.

| Item | What to do |
| --- | --- |
| **History** (`HistoryPoint[]`) | Today it runs 2011 to 2025. With v1.1 it runs 2007 to 2025: 2007 to 2010 have pay but `jobs_k` is `null` (flags `bridged_soc2000`, `bridged_soc2010`); job counts start in 2011. Any value can be `null`. Some careers have gaps (for example 2016 is missing for 3 of 20 today). Draw only the points that are present. Never interpolate and never assume one point per year |
| **Hedge `evidence`** | `title` (linked to ESCO through at least 3 job titles) or `estimate` (ISCO fallback). Show an "estimate" badge when it is `estimate`. In `schemas/HedgeCandidate.json` and `schemas/Hedge.json` |
| **`resilience_tech_slump`** | `pending` (value `null`) today. Real with v1.1, measured for a broad job-advert category. The `category_level` flag is must-mention: name the category from `extra.adverts_category` |
| **`exposure`** | When the `sources_disagree` flag is present (two independent research estimates disagree), show its sentence and the wider range. There is no separate field |
| **`exposure_uk`** | The DfE score as a percentile rank among UK occupations, 0 to 1, where 1 is the most exposed. A cross-check only: never show it as a second headline number. It is `pending` in today's `career_2451.json` |
| **`resilience_2008`** | `pending` (value `null`) today. Real with v1.1: the worse of the jobs change and the real pay change, April 2008 to April 2009. `extra` has both parts and says which one is the headline |
| **`young_worker_share`** | New optional metric (a fraction): the share of workers aged 16 to 24 in 2016, including the self-employed (ONS APS 2016). A card line if you want it; ignore it otherwise. A new key in `Career.metrics`: an absent key means missing (it is listed in `vocab.ML_METRICS`) |
| **`crises[].baseline_real_pay_median`** | Optional on a crisis (the 2008 one has it). In `schemas/Crisis.json` |

**Accessibility (ours, not Arsenii's).** Every chart needs a text version a screen reader can read, including the timeline.

## 7. The cards

Screens, from the project rules (`AGENTS.md`). The ones marked **never cut** stay in the demo, whatever else is dropped.

1. **Three picks vs her first idea** (never cut): Ambitious (highest return among good fits), Safe (lowest risk among
   good fits), Balanced (best return per unit of risk). Each pick has `components` and `vs_first_idea`.
   **"Did you mean...?"**: when `first_idea` is `null` and `first_idea_candidates` is not empty, her typed first idea matched
   several careers equally. Show the candidates (`soc2020`, `title`) as a list to choose from, then send the chosen SOC code
   as `first_idea` in a new request. Do not draw the comparison until she has chosen.
   **No match**: when `first_idea` is `null` and `first_idea_candidates` is empty, we could not match what she typed. This is
   different from "Did you mean...?". The response still has three picks. Show the free choice: let her retype, with a plain message such as
   "We could not find that job, try another word". It is not an error.
2. **The hedge** (never cut): a related career next to the top pick, with `risk_delta` (negative means safer) (`Hedge`).
3. **Backtest button** (never cut): pick a past year, see how earlier ratings held up. Show bad results as they are.
4. **Roadmap** (never cut): three steps and a "this month" action (`Roadmap`). Step 1 is worded by nation: Scotland "Take
   Higher <subjects>", England "Take A-level <subjects>", Wales and Northern Ireland "Take <subjects> at A-level or equivalent".
   Outside Scotland, step 2 has route `null` and the detail "Routes for this nation are missing from our data." Show that text.
5. **Provenance badges** (never cut): section 4.
6. **Pull the plug** (never cut): section 5.

Also: the automation-worry slider (`automation_worry`, 0 to 1, in `ProfileIn`).

## 8. What lands when

| When | What |
| --- | --- |
| Now | The API on `main` (sample and preliminary data), `docs/openapi.json`, these examples and the schemas |
| Sunday 08:00 to 10:00 | Real ML data (Arsenii v1.1) and the real career catalogue and routes. Values change, shapes should not |
| Sunday 11:30 | Code freeze |

Examples get regenerated when the data or the contract changes:

```
python -m avenir_contracts.examples
```

Run it from the repo root with the project installed (`pip install -e ".[dev]"`). It rewrites `schemas/` and `examples/`.

**Run the API** from `main`, from the repo root:

```
pip install -e ".[dev]"
uvicorn avenir_api.app:app --port 8000
```

CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`. Recommendations take about 10 ms locally, and the ad overlays
run in parallel.

## 9. Who to ask

| About | Ask |
| --- | --- |
| Contract and data shapes | Yehor |
| API behaviour | Nazar |
| ML numbers and flags | Arsenii |
