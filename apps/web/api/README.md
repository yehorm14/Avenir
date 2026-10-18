# Aventier app API

`api.application:app` is the served application. It combines the experience
endpoints with the canonical `/api/v1` decision API and wraps both in the shared
response envelope. It uses committed evidence and prepared guidance without API
keys or a live language model.

## Standalone backend and Vite development

From the repository root, with Python 3.12+ and Node 20+:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/web ci
npm --prefix apps/web run api
```

The editable installation makes the local contracts, decision engine, adapters
and canonical API packages available to the assembled app. The backend listens
at `http://127.0.0.1:8015`. Its interactive API documentation is at
`http://127.0.0.1:8015/docs`.

In a second terminal, from the repository root:

```sh
npm --prefix apps/web run dev
```

Open `http://127.0.0.1:4175`. Vite proxies `/api` to port 8015, so browser requests
stay on the frontend's origin. Run only one backend on port 8015
and one frontend on port 4175 at a time. The equivalent direct backend command,
from `apps/web`, is:

```sh
../../.venv/bin/python -m uvicorn api.application:app --host 127.0.0.1 --port 8015
```

For the single-process production launcher and setup on Windows, see the
[root README](../../../README.md).

## Response contract

Both API layers return `{ok, data, error, meta}`. Read successful payloads from
`data`; errors contain a code, message and field details. Metadata contains the
request ID, evidence date and source statuses. Unknown occupations return HTTP 404;
invalid inputs return HTTP 422. A snapshot-backed response can succeed while reporting
snapshot or missing source status.

For example, this request exercises the canonical decision endpoint:

```sh
curl -sS http://127.0.0.1:8015/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"profile":{"interests":["maths","design"],"nation":"scotland"},"first_idea":"architect"}'
```

## Experience endpoints

- `GET /api/health`: status, curated-career count, ML mode and guide mode.
- `GET /api/bootstrap`: 21 curated profiles (20 matched careers plus plumber),
  tags, original source registry, backtest, crises and data status.
- `GET /api/catalogue`: 412 lightweight occupation summaries for Jobs. Pay and
  employee-job counts retain their source and observation year; any older count
  is explicitly marked as the last available historical observation.
- `GET /api/careers/{soc}`: full occupation profile with exact supplied metrics,
  history and top-five hedge candidates. Current missing observations remain
  null; a separate display observation may show an older employee-job count.
- `POST /api/matches`: tags and pay/interest/need weights produce 20 ranked
  careers with supplied calibrated interest affinities. Plumber and the broader
  catalogue remain available for evidence browsing.
- `POST /api/discovery`: known-direction or exploring answers produce three
  options within the 20-career matching set, with assumptions and caveats.
- `GET /api/path/{soc}?nation=Scotland`: curated pathway example where available.
  Related-pathway bridges are disclosed. Course earnings remain null so
  illustrative prototype values do not replace occupation evidence. Unsupported
  routes return HTTP 404.
- `POST /api/guide`: `{ "soc": "2134", "message": "What skills can I build?",
  "history": [] }` returns prepared, source-linked guidance and explicitly
  identifies its mode. Broader profiles disclose unavailable detailed routes.

The canonical API also provides `/api/v1/tags`, `/api/v1/careers`,
`/api/v1/profile`, `/api/v1/recommendations`, history, hedges, routes, sources and
backtests. Inspect `/docs` or `/openapi.json` for their exact input/output models.
Canonical ranking excludes unreviewed sample catalogue metrics and route rows;
missing inputs reduce evidence coverage and confidence.

## Evidence and matching coverage

The imported ML evidence revision is Arsenii's
`a17aebbd7188c86ae01f521e89f7ba59855fd3e8` (contract v1.1). Later local matcher
reliability fixes are recorded in this repository's Git history. Evidence covers
412 occupations; histories span 2007–2025 with employee-job counts from 2011.
The 2021 occupation-code break, older-code bridges, wider-group estimates,
provisional values and missing observations retain their supplied flags and
notes. Pay covers full-time employees; each employee-job metric states its own
coverage. Self-employed workers require separate evidence.

The experience matcher uses the 20-career affinity set. Fit is the mean supplied
tag affinity; pay and need use available median-pay and observed-demand
percentile ranks. Scores run 0–100. Missing inputs are excluded from the weighted
mean and all-zero weights use equal importance. Demand describes historical
employment, rather than predicting future vacancies. Fit/hedge status, method,
evaluation limits and real/mock origin are reported in the payload. Unknown tags
return HTTP 422. Curated study routes, university examples and opportunities retain
their coverage notes; they are not a live calendar or university ranking.

## Verification

From the repository root:

```sh
.venv/bin/python -m pytest apps/web/api/tests -q
.venv/bin/python -m pytest
```

The app tests cover the assembled envelope, both API layers, no-key decisions,
static UI and raw internal experience behavior. The repository suite covers the
underlying packages. `api.main:app` is the internal experience app used by some
low-level tests; use `api.application:app` when serving the complete product.
