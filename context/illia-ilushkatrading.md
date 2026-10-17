# Illia: Aventir app and mock backend

- **Owner:** Illia / Codex
- **Branch:** `ilushkatrading`
- **Status:** ready for review

## Task

Publish Illia's existing Aventir career-exploration app and offline mock backend to Avenir on the explicitly requested branch. Created from the existing local Avenir main; no pull, fetch or merge was performed against Avenir.

## Included

- Standalone React/Vite frontend and FastAPI backend in `apps/aventir/`.
- Search, filters, pagination, career selection, skills/pay/industry charts, shortlist and research panel.
- Explicit mock/live modes. Mock mode uses bundled fixtures for 20 careers and four frozen industry histories, plus labelled deterministic reflections. No key, database import or provider call is needed at runtime.
- Optional full ESCO/ONS import and backend-only OpenAI integration for live mode. Runtime databases and credentials are excluded.
- Setup instructions, fixture generator, 18 tests and screenshot evidence.

This publishes the existing prototype as a separate app; it does not replace `apps/web`, `services/api`, the decision layer or Arsenii's ML slice. It does not yet implement the canonical shared response envelope or connect to the ML artefacts. Python formatting/imports were aligned with Avenir's Ruff rules; Python 3.12 is the published runtime.

## Validation

- 18 API/data/mock tests pass from the exported app without a database or environment file.
- Fresh offline `npm ci`, frontend format check and production build pass.
- Ruff and `make check` pass. The optional gitleaks executable is unavailable; a separate scan checked all added files against configured credentials and token patterns and found none.
- Prior browser verification includes 13 mock interactions and desktop/mobile accessibility snapshots scoring 100. The original local preview remains available in mock mode.

## Boundaries

The sample data is a frozen subset, not complete UK evidence. Salary and hiring coverage is partial and labelled. Industry vacancy counts are not occupation employment counts or forecasts. Mock reflections are not live AI. The real import can expose missing source skills; gaps remain explicit.

No secrets, raw downloads, databases, dependencies or build outputs are included. The original dirty workspace is preserved. Review before integrating this standalone prototype with the shared app and contracts.
