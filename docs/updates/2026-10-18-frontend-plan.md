# Frontend plan after the backend merge (Sat 17 Oct, late)

For Illia and Maksym, who have not followed the backend, and for Nazar and Yehor, who will pair with them.
Code freeze is **Sunday 18 Oct, 11:30**. The detailed handoff is `docs/frontend/README.md`. This page is the plan.

## 1. TL;DR

- The backend is mostly on `main`: contract v2.1, the decision engine, live adapters, catalogue ETL, the frontend pack.
- Nazar's API (PR #9) is ready but not merged yet. Until it is, run it from the `nazar/api` branch.
- Everything you see today is **sample data**, with `status: "mock"` and `source: "MOCK"`. Shapes are final. Values move on Sunday.
- Proposal (confirm at standup): Illia's app is the base and talks to our API. Two pairs build the screens.
- `apps/web/` is empty. Nothing in the UI is on our response envelope yet. That is the first job.

## 2. What the backend gives you today

All endpoints are under `/api/v1` and answer with the same envelope (`docs/frontend/README.md` section 2).
Paths come from `routes_read.py` and `routes_write.py` on `origin/nazar/api`. The contract is `docs/contracts.md`.

| Screen | Endpoint | Status |
| --- | --- | --- |
| Interest checklist | `GET /api/v1/tags` | Works on sample data |
| Interests from free text | `POST /api/v1/profile` | Works. No keys exist, so suggestions come from the fallback suggester |
| Three picks vs first idea, roadmap, explanation | `POST /api/v1/recommendations` | Works on sample data |
| "Did you mean...?" | same, `first_idea_candidates` | Works. `first_idea` is `null` when it fires |
| Career card | `GET /api/v1/careers/{soc}` | Works on sample data. `ads_now` is "missing" (no Adzuna key) |
| Career list (20 demo careers) | `GET /api/v1/careers` | Works. Confirm the 20 (section 7) |
| History chart | `GET /api/v1/careers/{soc}/history` | Works on sample data |
| Hedge | `GET /api/v1/careers/{soc}/hedge` | Works. Also inside the recommendation |
| Routes into a career | `GET /api/v1/routes/{soc}?nation=scotland` | Sample routes only. Real routes after Sunday 08:00 |
| Crises | `GET /api/v1/crises` | Works on sample data |
| Backtest button | `GET /api/v1/backtest/years`, `GET /api/v1/backtest?year=2013` | Works on sample data |
| Sources page, badge lookups | `GET /api/v1/sources` | Works. Licences not all checked yet |
| Pull the plug | `POST /api/v1/demo/live` with `{"enabled": false}` | Works. Today it switches off Adzuna ads only (section 7) |
| Health | `GET /health` | Works. `ml_mode` says real, mock, mixed or missing |
| Live job adverts (`ads_now`) | inside career and recommendation | Missing until someone has an Adzuna key |

Errors: malformed SOC is 422 `VALIDATION_ERROR`, unknown SOC is 404 `NOT_FOUND`. A snapshot is never an error.

### Run the API

```
git switch nazar/api
pip install -e ".[dev]"
uvicorn avenir_api.app:app --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive page. CORS allows `http://localhost:5173` and
`http://127.0.0.1:5173` (Vite's default port), from `services/api/avenir_api/app.py`. After #9 merges, switch back to `main`.

### Where the types come from

| When | Source |
| --- | --- |
| Now | `docs/frontend/schemas/*.json` (for example with `json-schema-to-typescript`) |
| After #9 | `docs/openapi.json`. Generate from it and drop `schemas/` |

Offline fixtures: `docs/frontend/examples/*.json`. They hold the `data` part unless the name starts with `envelope_` or `error_`.
Never edit them by hand. Regenerate with `python -m avenir_contracts.examples`.

## 3. Real versus sample data, and what flips on Sunday

| Thing | Today | Sunday | What you do |
| --- | --- | --- | --- |
| ML numbers (pay, demand, exposure, resilience, hedges, backtest) | Sample (`MOCK`) | Arsenii's real data, one PR, 08:00-09:30 | Nothing. Shapes stay compatible, values move |
| Career catalogue (20 careers) and routes | Sample | Real, after the team fills the CSVs at 08:00 | Re-check cards and route lists |
| Live job adverts (Adzuna) | "missing", no key | Live only if someone has a key | Show the badge as the API sends it |
| AI-written explanation | Template text, `ai_written: false` | Same, unless someone has an LLM key | Show "AI-written, check the source" when `true` |
| `AVENIR_FREEZE=1 pytest` | Fails on purpose | Green around 10:00 | Backend concern |
| Frontend pack in `docs/frontend/` | Sample-based | Regenerated around 09:30 | Re-pull types and fixtures |

Amira's flow on sample data (first idea "architect"): ambitious 2141 Web designer, safe 2452 Architectural technologist or planner,
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
| History chart | Job-count line breaks at 2021 (`recoded_2021`). Pay only before 2011. Dashed for `bridged_*`, marker on 2020. Null points are not drawn. Has a text version for screen readers |
| Backtest button (never cut) | Pick a year from `/backtest/years`, see the result. Bad results are shown as they are. Caveats visible. Text alternative for any chart |
| Sources page | Lists `registry` with attribution ("Jobs by Adzuna", ONS OGL, and the rest of `AGENTS.md` section 7) |

### Pair B: acceptance criteria

| Screen | Done when |
| --- | --- |
| Quiz | Interests from `/tags`, optional free text through `/profile`, first-idea input, automation-worry slider (0 to 1) |
| Three picks vs first idea (never cut) | Ambitious, Safe and Balanced cards, each with `components` and `vs_first_idea`. The first idea is shown beside them |
| "Did you mean...?" | When `first_idea` is `null` and `first_idea_candidates` is not empty, show the candidates. Send the chosen SOC as `first_idea` in a new request. Draw no comparison until then |
| Hedge (never cut) | Related career next to the top pick, with `risk_delta` (negative means safer). "estimate" badge when `evidence` is `estimate`. Copy says "closest skills", not "lower risk" |
| Roadmap (never cut) | Three steps plus a "this month" action. Routes show their `nation` |
| Notices and explanation | `notices` are visible. AI text is labelled "AI-written, check the source" |
| Pull the plug (never cut) | A button calls `POST /api/v1/demo/live` with `{"enabled": false}`. The ads badge flips from live to snapshot and the page does not break |
| Errors | `ok: false` shows a calm message. Error envelopes can have empty `meta.sources` |

### Everyone

- Wording: "worth exploring". Never "you should", "don't" or "AI will take this job". Exposure is not job loss.
- No secrets in the frontend (`AGENTS.md` rule 10).
- A working end-to-end demo beats extra features.

## 5. Build order with times (proposal)

| When | Pair A (Illia + Yehor) | Pair B (Maksym + Nazar) |
| --- | --- | --- |
| Tonight to 01:00 | Move the app to `apps/web/`, remove the mock backend, generate types from `docs/frontend/schemas`. One typed envelope client. Career card from `/careers/{soc}` with the badge component and the metric rules | Run the API from `nazar/api`. Quiz calling `/tags` and `/profile`. Post to `/recommendations` and render three picks vs the first idea |
| 01:00 | API serves Amira's flow on sample data. Switch types to `docs/openapi.json`. Codex integration run | Same. Add hedge and roadmap |
| Sun 08:00 to 09:30 | Real data lands. Fill the catalogue and routes CSVs with the team. History chart, flags, backtest button, sources page | "Did you mean...?", pull the plug button, error states. Fill CSVs with the team |
| Sun 09:30 to 10:00 | Regenerate the pack and types. Re-check every card against real values | Same for the quiz flow. Nazar fixes backend tests that hard-coded sample values |
| Sun 10:00 to 11:30 | Rehearse the flow and pull the plug. README sections for the frontend. Fix only what breaks the demo | Same. Text alternatives and wording pass |
| Sun 11:30 | Freeze | Freeze |

## 6. What we need from you

1. **Owner names in `AGENTS.md`.** The "Frontend and glue" row says TBD. A human edits it. Agents do not.
2. **Connect to the envelope.** Read `data` when `ok` is true, `error` when it is false. Show `meta.sources` as badges.
3. **The badges.** Section 4 above and `docs/frontend/README.md` sections 4 and 5. Without them a number does not ship.
4. **The wording rules.** Section 4, "Everyone".
5. **Arsenii's UI asks:**
   - Break job-count lines at 2021.
   - History runs 2007 to 2025, job counts from 2011.
   - "estimate" badge on hedges with `evidence: "estimate"`.
   - Show "category level" for `resilience_tech_slump`.
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
| 1 | Pull the plug also switches off Adzuna, the LLM and Arsenii's matcher service, with a badge each | Today `/demo/live` switches Adzuna only. More badges to show |
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
