# Deploy

- Docker: `docker compose up --build` serves the app on port 4175. The image reads `$PORT` (default 4175).
- Render: [render.yaml](../render.yaml) defines a free-plan Docker web service built from `apps/web/Dockerfile`, with `/health` as the health check.
- Production smoke check: run `bash scripts/smoke-production.sh` from the repo. CI runs the same script. It builds the Render image, starts it without optional keys or outbound networking, and checks the app shell and JavaScript, health, bundled bootstrap evidence and a career comparison. On failure it prints the container logs.

## Publishing the public demo

No hosted URL is verified yet, so the README does not link one. To publish it:

1. Deploy the Render blueprint ([render.yaml](../render.yaml)); no secrets or API keys are needed. The free plan sleeps when idle, so the first request can take a minute.
2. Check the deployed URL with `curl -fsS "$DEMO_URL/health"`, then open it signed out in a private window and complete the example: **Use Amira’s example profile**, then the matches, the evidence comparison and **My plan**, then **Start a fresh session**. Set `DEMO_URL` to your own service URL; do not commit placeholders as if they were live.
3. Only after that works, add the URL to the README "Try the demo" section. The recorded walkthrough in [docs/demo](demo/README.md) was captured against the local production image, not a hosted URL.

## Optional environment variables

The chatbot calls an LLM only when `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` (or `ANTHROPIC_API_KEY`) are set in the process environment. The app does not read a `.env` file. All names are listed in [.env.example](../.env.example).

## Known limits

- Interest affinities and occupation mappings are preliminary; matcher development labels are synthetic, so no matching accuracy is claimed.
- Median pay is for full-time employees, not starting pay. Routes and organiser links are curated examples.
- The plan lives only in the browser: no accounts and no cross-device sync.
- `prototypes/pathfinder-game/backend` is a legacy module that the app still imports.
