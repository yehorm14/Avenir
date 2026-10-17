# Aventir

Sprint 1: a single career research screen, built with React and FastAPI. The dark chart overview and white career browser follow Illia's [Trading 212 reference](https://community.trading212.com/t/your-home-screen-just-got-a-new-look/87886/3).

## Run the mock backend

With dependencies installed and the React build ready, run this from the repository root:

```sh
cd apps/aventir/api
AVENTIR_MODE=mock python3 -m uvicorn aventir.main:app --host 127.0.0.1 --port 4174
```

Open http://127.0.0.1:4174. Mock mode uses the bundled `api/fixtures/demo.json`: 20 sample careers and four frozen industry-history series. Search, filters, pagination, detail, charts, shortlist and research use the same API as live mode. Research responses are deterministic samples, explicitly labelled in the UI. No database import, API key or external service call is needed at runtime, even if a key already exists in `.env`.

The sample catalogue is a frozen subset of official data. Its count is shown as 20, with a persistent demo banner; it does not claim full catalogue coverage. To regenerate the fixtures after a live import, run `python3 scripts/make_demo.py` from `api/`.

Set `AVENTIR_MODE=live` to use the full SQLite catalogue and optional OpenAI connection. Invalid mode values fail clearly; live errors never silently substitute sample data. `/api/health` reports the mode, `ai_configured` and `research_available` separately.

## Install and run live mode

Python 3.12+ and Node 20.19+ are required. From this directory:

```sh
cd api
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/import_data.py
cd ../web
npm ci
npm run build
cd ../api
AVENTIR_MODE=live python3 -m uvicorn aventir.main:app --host 127.0.0.1 --port 4174
```

Open http://127.0.0.1:4174. The importer caches successful ESCO batches, verifies the unique career count against the source total, imports ONS observations and replaces the database atomically. The initial official import can take several minutes. Re-running reuses the ignored `api/data/raw/` cache; remove that directory to fetch a fresh catalogue. Database files and raw caches are ignored by Git.

For development, run FastAPI on port 8174 and `npm run dev` in `web/`. Vite proxies `/api` to FastAPI. No CORS wildcard or browser API credential is needed.

## Server-side AI connection

Copy `api/.env.example` to `api/.env`, set `OPENAI_API_KEY` locally and restart FastAPI. Use a replacement for any key previously shared in chat. Keep the file private (`chmod 600 api/.env`). The file is ignored by Git. Never put a key in a `VITE_` variable.

`OPENAI_MODEL` defaults to `gpt-4.1-mini`. The API uses the OpenAI Responses API with a validated structured reflection. Calls happen only after pressing **Explore this career**. The backend retrieves the selected career's evidence itself; the model does not generate chart data. The service permits at most eight research requests per minute across this local process. AI availability is explicit, and provider errors are sanitised. Without a key, the complete career browser and charts remain usable.

This is a local hackathon app. Public hosting would also need account controls, per-user quotas and deployment configuration.

## What the graphs mean

- **Industry hiring:** actual ONS UK vacancy observations, with source values converted from thousands to absolute vacancies. Each dated point is a three-month average. Reviewed mappings provide broad industry context; they do not measure a specific occupation's demand or predict job security. The time ranges use the latest observation, not today's date.
- **Skills:** counts of essential skills, essential knowledge and optional relationships from the official ESCO occupation profile. These are not a student's aptitude or a fit score.
- **Pay:** individually matched National Careers Service starter-to-experienced annual references, with their official profile links. No salary time series, inferred salaries or invented forecasts.
- **Gaps:** a European taxonomy is not complete UK labour-market coverage. Unmatched salary/hiring data stays unavailable. If malformed upstream skill data prevents a full profile response, retain its official identity and mark skills unavailable rather than displaying zero requirements.

Sources, retrieval dates, release dates and exact chart observations are inspectable inside the app. Shortlists are stored on the current device. University, college and apprenticeship exploration links lead to official guidance; current openings and eligibility are not asserted.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Local readiness and whether AI credentials are configured; no secret values |
| `GET /api/meta` | Catalogue coverage, retrieval metadata, groups and imported industry series |
| `GET /api/careers?q=&group=&offset=0&limit=8` | Literal title/alias search, group filter and pagination |
| `GET /api/careers/{esco-id}` | Full career, source relationships, reviewed pay and industry context |
| `POST /api/research` | `{career_id, question?}` to structured evidence-based AI reflection |

FastAPI's interactive schema is at `/docs`. Shared team contracts remain untouched; these are app-local interfaces.

## Verify

```sh
cd api
python3 -m pytest -q
cd ../web
npm run format:check
npm run build
```

See `VERIFICATION.md` for observed results and screenshot evidence. The previous implementation remains in `apps/pathfinder/`. Quiz, personal scoring, accounts and further pages are outside this sprint. The research-platform pitch stays in team documentation, outside the product UI.
