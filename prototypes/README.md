# Prototypes

Hackathon experiments kept for reference. **This folder is not the shipped app, and nothing here is deployed as its own service.**

The shipped product is:

| Part | Folder |
|---|---|
| React frontend | `apps/web` |
| Web API that serves the frontend and the experience endpoints | `apps/web/api` |
| Canonical `/api/v1` decision API | `services/api` |
| Decision rules, ML, contracts, adapters and ETL | `packages/` |

## Contents

- `pathfinder-game/` is the earlier Pathfinder prototype's Python backend. It is not run as a separate service, but `apps/web/api` still imports its `app.data` and `app.path` modules to build career pathways (the web Docker image copies the backend for that reason), so it stays in the tree until that code moves into `packages/`. See [pathfinder-game/README.md](pathfinder-game/README.md).

Its tests run as part of `make test`.
