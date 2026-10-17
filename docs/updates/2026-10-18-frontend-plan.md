# Frontend plan after the backend merge (Sat 17 Oct, late)

For Illia and Maksym, who have not followed the backend, and for Nazar and Yehor, who will pair with them.
Code freeze is **Sunday 18 Oct, 11:30**. The detailed handoff is `docs/frontend/README.md`. This page is the plan.

## 1. TL;DR

- The backend is on `main`: contract v2.1, the decision engine, live adapters, catalogue ETL, the frontend pack and Nazar's API (PR #9 and PR #14).
- Run the API from `main`. `docs/openapi.json` is published.
- Today: pay, demand, exposure and the backtest are real but preliminary (status `preliminary`). Job names, subjects, routes, hedges, the interest list and live ads are sample data (`mock`). `resilience_2008` and `resilience_tech_slump` are `pending`. Shapes are final; values move on Sunday.
- Proposal (confirm at standup): Illia's app is the base and talks to our API. Two pairs build the screens.
- `apps/web/` is empty. Nothing in the UI is on our response envelope yet. That is the first job.

## 2. What the backend gives you today

All endpoints are under `/api/v1` and answer with the same envelope (`docs/frontend/README.md` section 2).
Paths come from `services/api/avenir_api/routes_read.py` and `routes_write.py` on `main`. The contract is `docs/contracts.md`.

| Screen | Endpoint | Status |
| --- | --- | --- |
| Interest checklist | `GET /api/v1/tags` | Works. Sample interest list (`ml_fit` is `mock`) |
| Interests from free text | `POST /api/v1/profile` | Works. No keys exist, so suggestions come from the fallback suggester |
| Three picks vs first idea, roadmap, explanation | `POST /api/v1/recommendations` | Works. Preliminary ML numbers, sample names. Takes about 10 ms locally |
| "Did you mean...?" | same, `first_idea_candidates` | Works. `first_idea` is `null` when it fires |
| No match for the first idea | same | Works. `first_idea` is `null` and `first_idea_candidates` is empty. Show the free choice (section 4, Pair B) |
| Career card | `GET /api/v1/careers/{soc}` | Works. ML metrics preliminary, names and subjects sample. `ads_now` is a sample number (`status: "mock"`, `source: "MOCK"`, `meta.sources` adzuna `mock`) until a key exists |
| Career list (20 demo careers) | `GET /api/v1/careers` | Works. Confirm the 20 (section 7) |
| History chart | `GET /api/v1/careers/{soc}/history` | Works. Preliminary ML data. 2011 to 2025 today, with gaps for some careers (section 6) |
| Hedge | `GET /api/v1/careers/{soc}/hedge` | Works. Sample hedges until Arsenii's data lands; `evidence` is `null` today. `data` is `null` for 4 of 20 careers. Also inside the recommendation |
| Routes into a career | `GET /api/v1/routes/{soc}?nation=scotland` | Sample routes only, and only for `scotland`: other nations return `[]`. Real routes after Sunday 08:00 |
| Crises | `GET /api/v1/crises` | Works. Preliminary ML data |
| Backtest button | `GET /api/v1/backtest/years`, `GET /api/v1/backtest?year=2013` | Works. Preliminary ML data |
| Sources page, badge lookups | `GET /api/v1/sources` | Works. Licences not all checked yet |
| Pull the plug | `POST /api/v1/demo/live` with `{"enabled": false}` | The call works and returns `{live}`. Today it changes nothing visible, because ads are `mock` (section 7) |
| Health | `GET /health` | Works. `ml_mode` says real, mock, mixed or missing |
| Live job adverts (`ads_now`) | inside career and recommendation | Sample (`mock`) until someone has an Adzuna key. With a key it is `live`, then `snapshot` after the switch is off. The ad overlays run in parallel |

Errors: malformed SOC (`abc`, `245`) is 422 `VALIDATION_ERROR`, a well-formed unknown SOC (`9999`) is 404 `NOT_FOUND`. A snapshot is never an error.

Empty and null are not errors. Routes are `[]` for nations other than `scotland` today. Hedge is `null` for 4 of 20 careers ("no safer related career found"). Show a plain message in both cases.

### Run the API

```
pip install -e ".[dev]"
uvicorn avenir_api.app:app --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive page. CORS allows `http://localhost:5173` and
`http://127.0.0.1:5173` (Vite's default port), from `services/api/avenir_api/app.py`. Run it from the repo root on `main`.

### Where the types come from

| When | Source |
| --- | --- |
| Now | `docs/openapi.json`. Generate from it: `npx openapi-typescript@7.4.4 docs/openapi.json -o src/api.d.ts` (this output passes `tsc --strict`). `data` is optional in the types, so narrow on `ok` in the client. `docs/frontend/schemas/*.json` are offline reference only |

Offline fixtures: `docs/frontend/examples/*.json`. They hold the `data` part unless the name starts with `envelope_` or `error_`.
Never edit them by hand. Regenerate with `python -m avenir_contracts.examples`.

## 3. Real versus sample data, and what flips on Sunday

| Thing | Today | Sunday | What you do |
| --- | --- | --- | --- |
| ML numbers (pay, demand, exposure, backtest) | Real but preliminary (`preliminary`) | Arsenii's final data, one PR, 08:00-09:30 | Nothing. Shapes stay compatible, values move |
| `resilience_2008`, `resilience_tech_slump` | `pending`, value `null` | Real with Arsenii's v1.1 | Show "not available yet" from `status` |
| Hedges, the interest checklist and fit scores (`ml_hedges`, `ml_fit`) | Sample (`mock`). Hedge `evidence` is `null`. Wellbeing, stress and shortage are `mock` too | Hedges and `evidence` become real with Arsenii's Sunday PR. `ml_fit` may stay a placeholder | Show the badge from `status` |
| History | 2011 to 2025, some careers have gaps (2016 is missing for 3 of 20) | 2007 to 2025 with Arsenii's v1.1 (pay only before 2011) | Draw the points that exist. Never interpolate |
| Career catalogue (20 careers: names, subjects) and routes | Sample (`mock`) | Real, after the team fills the CSVs at 08:00 | Re-check cards and route lists |
| Live job adverts (Adzuna) | Sample (`mock`), no key | `missing` once the real catalogue is built, unless someone has Adzuna keys | Show the badge as the API sends it |
| AI-written explanation | Template text, `ai_written: false` | Same, unless someone has an LLM key | Show "AI-written, check the source" when `true` |
| `AVENIR_FREEZE=1 pytest` | Fails on purpose | Green around 10:00 | Backend concern |
| Frontend pack in `docs/frontend/` | Sample-based | Regenerated around 09:30 | Re-pull types and fixtures |

Amira's flow today (first idea "architect"): ambitious 2141 Web designer, safe 2452 Architectural technologist or planner,
balanced 2453 Quantity surveyor, hedge 2123 Electrical engineer. These will change when real data lands. Do not hard-code them.

## 4. One app, two pairs (proposal, confirm at standup)

**Base:** Illia's React + Vite explorer (branch `ilushkatrading`, folder `apps/aventir/`). Move it to `apps/web/`,
which is where `AGENTS.md` says the frontend lives. Drop its mock FastAPI backend. Point it at our API. Use
`docs/frontend/examples/` as offline fixtures.

**Pair A: Illia + Yehor.** Career card, history chart, provenance badges, sources page.
**Pair B: Maksym + Nazar.** Quiz, three picks vs first idea, hedge, roadmap, "Did you mean...?".
Backtest and pull the plug are never-cut and have no owner yet. Proposal: backtest to Pair A, pull the plug to Pair B.

### Pair A: acceptance criteria

| Screen | Done when |
| --- | --- |
| Provenance badges (never cut) | Every number shows source name plus `as_of`, a confidence badge, and the `meta.sources` status (`live`, `snapshot`, `mock`, `missing`) |
| Metric states | `mock` shows "sample data". `preliminary` shows a tag. `pending` shows "not available yet". `value: null`, an absent key, or `suppressed` shows "missing", never 0 or blank |
| Group-level data | `granularity: "major_group"` shows a "job group" badge. `wellbeing` and `stress` are always group-level |
| Ranges | `low` and `high` show as a range |
| Flags | Each flag shows its sentence from `examples/flags.json`. `must_mention` flags are visible on the card, not in a tooltip |
| Career card | Exposure is labelled "Automation exposure (research estimate)". England-only items carry an "England" label. `shortage` reads "UK (some indicators GB)" |
| History chart | Job-count line breaks at 2021 (`recoded_2021`). Pay only before 2011. Dashed for `bridged_*`, marker on 2020. Null points and missing years are not drawn and never interpolated. Has a text version for screen readers |
| Backtest button (never cut) | Pick a year from `/backtest/years`, see the result. Bad results are shown as they are. Caveats visible. Text alternative for any chart |
| Sources page | Lists `registry` with attribution ("Jobs by Adzuna", ONS OGL, and the rest of `AGENTS.md` section 7) |

### Pair B: acceptance criteria

| Screen | Done when |
| --- | --- |
| Quiz | Interests from `/tags`, optional free text through `/profile`, first-idea input, automation-worry slider (0 to 1) |
| Three picks vs first idea (never cut) | Ambitious, Safe and Balanced cards, each with `components` and `vs_first_idea`. The first idea is shown beside them |
| "Did you mean...?" | When `first_idea` is `null` and `first_idea_candidates` is not empty, show the candidates. Send the chosen SOC as `first_idea` in a new request. Draw no comparison until then |
| No match | When `first_idea` is `null` and `first_idea_candidates` is empty, we could not match what she typed (for example "manager" or `9999`). This is not "Did you mean...?". Show the free choice and a plain message. There are still three picks. No error |
| Hedge (never cut) | Related career next to the top pick, with `risk_delta` (negative means safer). "estimate" badge when `evidence` is `estimate` (`evidence` is `null` today). Copy says "closest skills", not "lower risk". Hedge `null` shows "no safer related career found" |
| Roadmap (never cut) | Three steps plus a "this month" action. Routes show their `nation`. Step 1 by nation: Scotland "Take Higher <subjects>", England "Take A-level <subjects>", Wales and Northern Ireland "Take <subjects> at A-level or equivalent". Outside Scotland, step 2 has route `null` with "Routes for this nation are missing from our data." Show it as plain text |
| Notices and explanation | `notices` are visible. AI text is labelled "AI-written, check the source" |
| Pull the plug (never cut) | A button calls `POST /api/v1/demo/live` with `{"enabled": false}`, gets `{live}` back, and the page does not break. The badge flip (`adzuna` in `meta.sources` and the `ads_now` badge from live to snapshot) is pending the pull-the-plug decision (section 7): today ads are `mock`, so nothing visible changes |
| Errors | `ok: false` shows a calm message. Error envelopes can have empty `meta.sources` |

### Everyone

- Wording: "worth exploring". Never "you should", "don't" or "AI will take this job". Exposure is not job loss.
- No secrets in the frontend (`AGENTS.md` rule 10).
- A working end-to-end demo beats extra features.

## 5. Build order with times (proposal)

| When | Pair A (Illia + Yehor) | Pair B (Maksym + Nazar) |
| --- | --- | --- |
| Tonight to 01:00 | Move the app to `apps/web/`, remove the mock backend, generate types from `docs/openapi.json`. One typed envelope client that narrows on `ok`. Career card from `/careers/{soc}` with the badge component and the metric rules | Run the API from `main`. Quiz calling `/tags` and `/profile`. Post to `/recommendations` and render three picks vs the first idea |
| 01:00 | API serves Amira's flow end to end. Generate types from `docs/openapi.json` from the start. Codex integration run | Same. Add hedge and roadmap |
| Sun 08:00 to 09:30 | Real data lands. Fill the catalogue and routes CSVs with the team. History chart, flags, backtest button, sources page | "Did you mean...?", pull the plug button, error states. Fill CSVs with the team |
| Sun 09:30 to 10:00 | Regenerate the pack and types. Re-check every card against real values | Same for the quiz flow. Nazar fixes backend tests that hard-coded today's values |
| Sun 10:00 to 11:30 | Rehearse the flow and pull the plug. README sections for the frontend. Fix only what breaks the demo | Same. Text alternatives and wording pass |
| Sun 11:30 | Freeze | Freeze |

## 6. What we need from you

1. **Owner names in `AGENTS.md`.** The "Frontend and glue" row says TBD. A human edits it. Agents do not.
2. **Connect to the envelope.** Read `data` when `ok` is true, `error` when it is false. Show `meta.sources` as badges.
3. **The badges.** Section 4 above and `docs/frontend/README.md` sections 4 and 5. Without them a number does not ship.
4. **The wording rules.** Section 4, "Everyone".
5. **Arsenii's UI asks:**
   - Break job-count lines at 2021.
   - History runs 2011 to 2025 today and 2007 to 2025 with Arsenii's v1.1 (pay only before 2011, job counts from 2011). Years can be missing (for example 2016): draw only the points present.
   - "estimate" badge on hedges with `evidence: "estimate"`.
   - Show "category level" for `resilience_tech_slump` (`pending` today).
   - Show "sources disagree" and the wider range for `exposure`.
   - Give every chart a text alternative.
   - Hedges mean "closest skills", not "lower risk".
   - Track record means "how simple rules held up".
6. **Check and rotate possible keys.** Codex's secret scan flagged 2 possible keys in `Advisers.tsx` in Maksym's prototype
   (branch `max/pathfinder-prototype`). Maksym: check them. If they are real, rotate them. Do not copy that file into `apps/web/`.

## 7. Open decisions that affect the UI

Proposals from Yehor, to settle with the team.

| # | Decision | Effect on the UI |
| --- | --- | --- |
| 1 | Pull the plug also switches off Adzuna, the LLM and Arsenii's matcher service, with a badge each | Today `/demo/live` is about Adzuna only, and ads are `mock`, so nothing visible changes. More badges to show |
| 2 | Gemini free tier through the OpenAI-compatible adapter if anyone has a key, else template only | Decides whether "AI-written" ever appears in the demo |
| 3 | Constant caveats such as `employees_only` go in a card footer, not in `notices` or prose | Card footer component |
| 4 | 2008 crisis off the cards (Arsenii recommends), kept in "how we checked" | One less card element |
| 5 | Track-record label: "How simple rules held up" | Label text on the backtest |
| 6 | Arsenii's `validate_explanation` is not needed, the adapter check covers it | None |
| 7 | Confirm the 20 demo careers | The career list and fixtures |

## 8. Who to ask

| About | Ask |
| --- | --- |
| Contract, data shapes, catalogue, routes, live adapters, this plan | Yehor |
| API behaviour, decision engine, `docs/openapi.json` | Nazar |
| ML numbers and flags, Arsenii's summary in `docs/updates/2026-10-17-arsenii-ml.md` | Arsenii |
| Illia's app and Maksym's prototype | Illia, Maksym |
