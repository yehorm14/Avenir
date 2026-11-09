# Deploy

- Docker: `docker compose up --build` serves the app on port 4175. The image reads `$PORT` (default 4175).
- Render: [render.yaml](../render.yaml) defines a free-plan Docker web service built from `apps/web/Dockerfile`, with `/health` as the health check.
- The image has not been built in CI yet.

## Optional environment variables

The chatbot calls an LLM only when `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` (or `ANTHROPIC_API_KEY`) are set in the process environment. The app does not read a `.env` file. All names are listed in [.env.example](../.env.example).

## Known limits

- Interest affinities and occupation mappings are preliminary; matcher development labels are synthetic, so no matching accuracy is claimed.
- Median pay is for full-time employees, not starting pay. Routes and organiser links are curated examples.
- The plan lives only in the browser: no accounts and no cross-device sync.
- `prototypes/pathfinder-game/backend` is a legacy module that the app still imports.
