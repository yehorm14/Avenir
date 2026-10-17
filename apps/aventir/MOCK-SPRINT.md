# Mock backend increment

Requested by Illia on 17 October 2026. Keep React/Vite + FastAPI, with the same app-local API routes and response shapes.

- [x] Add tests proving the mock API works without a database or credentials and cannot invoke OpenAI.
- [x] Implement a fixture-backed repository and deterministic, explicitly labelled research responses. Preserve validation, 404 handling, search, group filters and pagination.
- [x] Add AVENTIR_MODE=mock; retain the existing live mode without silently substituting sample data on errors.
- [x] Show a compact demo-data label in the UI and identify sample reflections.
- [x] Run backend tests (18 passing), frontend build/format and Chrome DevTools checks (13 desktop interactions plus mobile audit). Mock mode is running at http://127.0.0.1:4174; desktop/mobile accessibility snapshots score 100.

Fixtures are a small frozen subset of the already imported official catalogue/history, not a claim of full catalogue coverage. No new pages or recommendation/ML models are part of this increment. Arsenii's slice and shared contracts stay unchanged. No agents or review gate are started.
