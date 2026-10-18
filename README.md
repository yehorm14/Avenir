# Aventier

A career decision and action plan for UK school leavers. Start with a career or a few interests, compare the evidence and trade-offs, choose three directions, then keep a practical plan with study routes, next actions and opportunities.

The hackathon demo follows Amira, 17, in Glasgow: maths and art, architecture as a first idea, and a question about how technology might change her options. The decision is which career to explore first and what to try this month.

## Run the complete product

Requires Node 20+ and Python 3.12+. Use a Python executable for that version or newer (`python3.13` in the tested local environment):

On macOS or Linux, prepare the complete app with `bash scripts/setup.sh`. It creates the local environment when absent, installs locked web dependencies and Python development dependencies, builds the app, then checks that both API layers and real evidence load. Recheck an existing setup with `bash scripts/check-setup.sh`.

Set `AVENIR_SETUP_PYTHON` to choose the Python executable used to create `.venv`. The separate `AVENIR_PYTHON` launcher override is for an already-prepared runtime environment.

Manual setup:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/web ci
npm --prefix apps/web run build
node scripts/run-app.mjs --production
```

Open [Aventier](http://127.0.0.1:4175). The production launcher serves the UI and both API layers from one process. No API keys, database, cloud account or external font service are required. Set `AVENIR_PYTHON` to use another Python environment; `AVENIR_PORT` changes the production port. Ctrl+C stops the service.

On Windows, create the environment with `py -3.13 -m venv .venv`, install with `.venv\Scripts\python.exe -m pip install -e ".[dev]"`, then use the same npm and Node commands.

For development, use `node scripts/run-app.mjs`: Vite runs on 4175 and proxies the combined API on 8015. `--preview` is an alias for the single-process production launcher after building.

The complete container definition is `docker compose up --build` (port 4175). It builds the web bundle, includes the committed snapshots and runs without keys as a non-root user. Container execution could not be verified on the current development machine because Docker is not installed. The optional standalone team API is available through `docker compose --profile api-only up api` on port 8000.

## What works

- Guided discovery, editable answers, three weighted options and three learner-ranked choices. Priorities change comparison indices; a known career stays visible as the reference.
- A searchable directory of all **412** supplied occupation profiles. Full evidence loads when a career is opened; personalised matching covers the **20** roles with supplied affinities.
- My plan remembers the route, personal reasoning, completed next actions and saved opportunities. Home offers resume. Download produces a readable HTML plan with source links; open it in a browser to print or save as PDF.
- University and earn-and-learn exploration, practical projects, transferable skills and curated organiser links. These are examples and discovery resources; availability and eligibility must be checked at the provider.
- The team's deterministic high-earnings, lower-risk and balanced comparisons, differences against the first idea, evidence confidence and a skill-overlap alternative when supported.
- Pay and employment histories, inflation adjustment, the 2021 occupation-code break, source notes, research exposure and historical backtest results, including negative outcomes.
- Prepared career guidance with per-response sources, retry, request cancellation and optional browser read-aloud. Keyboard controls, mobile layouts, reduced motion and text alternatives accompany the charts.

## Architecture and API

```mermaid
flowchart LR
  UI[React experience and browser-local plan] --> API[FastAPI application]
  API --> R[App priority ranking]
  API --> D[Team decision engine]
  API --> P[Provider and snapshot boundary]
  P --> M[Arsenii's committed evidence and model artefacts]
  P --> C[Curated pathway and organiser examples]
```

`apps/web/api/application.py` assembles the experience API, the canonical `/api/v1` API and the built UI. All served API responses use `{ok, data, error, meta}` with source statuses and request IDs. Explore [OpenAPI](http://127.0.0.1:4175/openapi.json) or [interactive API docs](http://127.0.0.1:4175/docs). The existing shared contract remains in [docs/contracts.md](docs/contracts.md); the assembled schema additionally describes `/api/bootstrap`, `/api/catalogue`, `/api/careers/{soc}`, `/api/discovery`, `/api/matches`, `/api/path/{soc}` and `/api/guide`.

Pure decision functions are in `packages/decision`. Provider interfaces and adapters remain separate in `packages/contracts`, `packages/adapters` and `packages/etl`. The product data boundary excludes synthetic catalogue metrics and unreviewed route rows from canonical ranking; genuine ML metrics are preserved. Unavailable catalogue inputs reduce coverage and confidence. No LLM ranks careers.

## Evidence and AI limits

ONS ASHE earnings and employment, ONS CPIH, ILO Working Paper 140, ESCO relationships and supplied UK demand context provide different perspectives. Every observation keeps its original source, date, geography, confidence and caveats. The latest available employment observation may be older than 2025 and is labelled with its actual year. Missing and suppressed observations remain unavailable. Median full-time employee pay excludes the self-employed and is not starting pay. Task exposure is not a job-loss probability; historical demand is not a forecast.

Interest affinities and occupation mappings are preliminary. Matcher development labels are synthetic; no validated accuracy or admissions eligibility is claimed. The historical backtest evaluates earlier market signals, not the personalised conversation or sliders. Curated routes are clearly identified as examples; the human-verified catalogue CSV is incomplete and has not been passed off as verified.

Codex helped integrate code, write editorial guidance, review changes and run verification. The runtime guide uses prepared source-based responses. Production explicitly uses template explanations, keyword suggestions and snapshot ads, so it remains functional without a live AI provider. The learner chooses priorities, career ranking, route and next actions. These choices are stored in the browser; there is no account, tracking or cross-device sync.

Source attribution: ONS (Open Government Licence); Skills England / DfE (OGL); ILO Working Paper 140 (Gmyrek et al., 2025); ESCO (European Commission); HESA / Discover Uni (CC BY 4.0), where used. The [source registry](snapshots/ml/sources.json) and [data manifest](data/manifest.yaml) retain coverage and licence notes. Optional Adzuna integrations retain Jobs by Adzuna attribution.

## Verify and demonstrate

```sh
PATH="$PWD/.venv/bin:$PATH" make check
```

The release gate covers Python lint, core/API/integration tests, web state/export tests, formatting, production build and a local secret scan. Browser evidence and actual limits are recorded in [apps/web/VERIFICATION.md](apps/web/VERIFICATION.md).

The [launch handoff](docs/launch/README.md) maps the product to the GUTS requirements. Use the [three-minute demo](docs/launch/demo-script.md) and [pilot/business case](docs/launch/business-case.md). Pricing, school adoption and pilot targets in that case are hypotheses, not traction or validated demand.

## Team integration

This branch combines Illia's finished frontend, Max's preserved Pathfinder prototype, Nazar's decision engine/API, Yehor's contracts/adapters and Arsenii's real occupation artefacts. Original commits retain their authorship. Earlier explorers remain under `apps/aventir` and `prototypes/pathfinder-game`; `apps/web` is the shipped experience. Read [AGENTS.md](AGENTS.md) before changing another slice.
