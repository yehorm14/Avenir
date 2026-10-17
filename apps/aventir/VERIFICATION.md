# Aventir sprint 1 — verification

The current preview has since switched to the mock backend increment described at the end of this record. The original live-data sprint evidence below is retained as historical verification.

Observed on 17 October 2026, on `codex/aventir-sprint-1`. Local work only; no commit, push, PR or public deployment. The final app is running at http://127.0.0.1:4174 using FastAPI and the production React build. The previous Pathfinder preview was stopped; its source remains intact.

## Build and tests

```text
python3 -m pytest -q
...........                                                              [100%]
11 passed in 0.51s

npm run format:check
All matched files use Prettier code style!

npm run build
vite v7.3.7 building client environment for production...
✓ 1587 modules transformed.
✓ built in 1.18s

git diff --check
(no output; exit 0)
```

Core tests cover official identity, source relationships, unavailable skills, thousands-to-vacancies conversion, sorting, missing/non-finite values, literal search metacharacters, pagination validation, missing careers, reviewed industry joins, missing pay, AI configuration, input validation, structured provider context and sanitised provider failures. The source transformations and API were checked failing before their implementation, then passing.

## Imported data

- ESCO source reported **2,942** occupations. SQLite contains **2,942 distinct IDs**. Every API pagination page was fetched in browser QA, reconciling all 2,942 records without duplicates.
- Official skill data is available for 2,937 profiles. Five profiles could not supply full essential-skill relationships. The importer isolates malformed upstream responses, preserves occupation identity and marks these profiles unavailable. The UI does not represent these gaps as zero requirements.
- **Six** individually reviewed NCS salary matches: software developer, data analyst, electrical engineer, civil engineer, land surveyor and mechanical engineer. The unmatched enrichment candidate is not counted or applied.
- **Four** ONS UK industry series, **303 actual observations each**: information and communication (JP9P), manufacturing (JP9I), construction (JP9L), human health and social work (JP9W).
- Verified increasing, unique dates, finite values, geography, industry granularity and units. The latest technology observation is **36,000 UK industry vacancies**, Jun–Aug 2026. This is a three-month average, not 36,000 software-developer openings.
- One-year, three-year and all-history chart views showed 13, 37 and 303 observations respectively. No salary histories or future observations are generated.

## Browser verification

Chrome DevTools MCP exercised the production app at 1440 × 1000 desktop and 390 × 844 mobile, including:

- All-catalogue coverage, source metadata, complete pagination, title/alias search and occupation-group counts.
- Career selection, pay/skills/hiring views, chart range changes and keyboard arrow navigation.
- Add/remove shortlist, filtered shortlist view and persistence after reload.
- Search for nurse-related titles, Armed forces filter (21 profiles), no-result state and recovery to all careers.
- A non-featured career (3D animator) showing its actual skill relationships, with unavailable pay and hiring tabs disabled.
- Civil engineer's unavailable source skills displayed explicitly while its reviewed construction context and salary reference remain usable.
- Source dialog open/close, official entry-route links and access to exact chart observations.
- Mobile catalogue recovery, career selection, skills graph and source dialog.
- No horizontal overflow at either viewport. No browser console warnings or errors on the final page.

Lighthouse snapshot audits on the final port 4174 app:

| Category | Desktop | Mobile |
| --- | ---: | ---: |
| Accessibility | 100 | 100 |
| Best practices | 100 | 100 |
| SEO | 100 | 100 |
| Agentic browsing | 100 | 100 |

These are snapshot accessibility/structure audits, not performance measurements or a guarantee of full accessibility conformance. The open mobile source dialog also passed its snapshot audit.

## OpenAI and credential handling

A minimal real Responses API call succeeded. The final UI also sent a specific question asking for three small coding projects and displayed a real structured response containing three project ideas and a follow-up question. Provider output remains labelled as AI reflection; source facts and chart numbers come from the database.

The credential is in the ignored backend `api/.env`, permissions **0600**. It is not in the frontend, generated assets, API source, tests or scripts (content scan: zero occurrences). Git ignore checks cover the environment, database and frontend build. The browser calls only the local research endpoint; no provider credential is sent to the frontend. Responses use `store=False`. The key shared in chat should be rotated and its replacement set locally in that file.

## Evidence and limits

- [Desktop with live AI reflection](artifacts/aventir-desktop.png)
- [Mobile](artifacts/aventir-mobile.png)
- [Desktop audit summary](artifacts/lighthouse-desktop.json)
- [Mobile audit summary](artifacts/lighthouse-mobile.json)

UK salary and industry coverage is partial and labelled. Industry context is a reviewed broad mapping, not occupation-level hiring data. Entry-route links are official guidance; current apprenticeship openings and eligibility were not imported. Shortlists are device-local. Quiz, personalised matching, accounts and subsequent pages remain outside this sprint. An in-house model has not been trained by this implementation.

## Mock backend increment — 17 October 2026

On `codex/aventir-mock-backend`, added an explicit `AVENTIR_MODE=mock` path serving the same API from bundled JSON. The preview at http://127.0.0.1:4174 now runs this mode. The sample contains 20 careers and four frozen history series. A persistent demo label, sample chart labels and sample research notices distinguish it from live data/AI. `AVENTIR_MODE=live` retains the full imported catalogue and optional provider connection.

Verification observed:

- **18 backend tests passed in 0.62s.** Seven new tests cover missing-database operation, refusing to initialise OpenAI even with a credential present, sample metadata, search/filter/pagination, deterministic research, request validation, unknown-career errors, explicit live-mode override and invalid-mode rejection. The new tests were observed failing before the feature existed.
- **Frontend build and format check passed.** Vite built 1,587 modules in 1.11s.
- **13 desktop browser checks passed**: backend mode/readiness, persistent demo badge, sample coverage, chart label, sample reflection, no missing-key error, all three chart types, shortlist, pagination, source disclosure and horizontal overflow.
- **Desktop and mobile Lighthouse snapshots score 100** for accessibility, best practices, SEO and agentic browsing. Final preview health reports `mode: mock`, `ai_configured: false`, `research_available: true`. No external provider request is required.
- The existing in-app preview was refreshed into mock mode. The temporary test server was stopped; the final mock server remains on port 4174.

[Mock backend screenshot](artifacts/aventir-mock.png). No commit, push, merge or public deployment.
