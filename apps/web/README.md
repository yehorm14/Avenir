# Aventier application

The complete React/Vite + FastAPI product lives here. See the [root setup and architecture](../../README.md) and [launch acceptance matrix](../../docs/launch/README.md).

From the repository root after installing dependencies:

```sh
npm --prefix apps/web run build
node scripts/run-app.mjs --production
```

Open http://127.0.0.1:4175. One service serves the UI, the experience API and the team's canonical `/api/v1` API using the shared envelope. `/docs`, `/openapi.json` and `/health` are on the same origin. No credentials are required. Use the launcher without `--production` for Vite development; both modes expose the same API format.

The user journey is known-direction or exploring conversation → three weighted options → three ranked choices → My plan. Route, personal note, completed actions and saved links persist in this browser. Plans export as source-linked HTML for sharing or printing. Jobs independently browses 412 supplied evidence profiles; 20 roles have calibrated interest affinities and curated detailed pathways. Broader profiles clearly state missing route/matching coverage.

`api/main.py` contains the internal experience endpoints; `api/application.py` assembles the served production application and wraps them in the canonical envelope. Low-level API tests preserve the original payload checks; assembled application tests exercise the real served envelope, both API layers, validation, no-key decisions and static UI. `api/product_data.py` excludes unreviewed sample catalogue inputs from ranking and lowers confidence for that absence. It preserves genuine ML observations.

The UI follows the user-selected QuantSoc direction in [docs/design.md](../../docs/design.md): local Inter, charcoal and silver, blue evidence accents and original gold signal paths. No external fonts, copied assets, decorative quotations or cursive typefaces are used.

```sh
npm --prefix apps/web test
npm --prefix apps/web run format:check
npm --prefix apps/web run build
.venv/bin/python -m pytest apps/web/api/tests
```

Numbers retain provenance and missing-data caveats. Ranking is deterministic; guide replies are prepared and cited, with cancellation and retry. No hosted LLM, live vacancy feed, starting-pay prediction or validated psychological assessment is claimed. The root README documents responsible AI, data coverage, attribution and the boundaries of the demo.
