# Avenir

**A portfolio manager for your future.** For a UK school leaver, Avenir finds careers that
fit, shows their return and risk with real UK data, says how sure it is, offers a hedge career,
maps the route in, and publishes how its own past ratings held up.

GUTS Hackathon 2026, Aladdin by BlackRock challenge: "One app. One clear decision."

> **Agents and humans: read [AGENTS.md](AGENTS.md) before writing anything.**

## Where things are

| Path | What |
| --- | --- |
| `AGENTS.md` | Rules for every AI agent and contributor |
| `docs/superpowers/specs/2026-10-18-avenir-design.md` | Full design (product, demo, data, decision layer, ML, risks) |
| `docs/contracts.md` | API contract (envelope, endpoints, models) |
| `docs/data-sources.md` | What data to fetch and how; what was checked |
| `data/manifest.yaml` | Every raw input with URL, method, licence |
| `context/` | One progress file per piece of work |
| `apps/web` | React + Vite frontend |
| `services/api` | FastAPI backend |
| `packages/decision` | Pure scoring: fit, return, risk, picks, hedge, roadmap |
| `packages/adapters/<source>` | One adapter per data source, each with a snapshot |
| `packages/ml` | Arsenii: ML data contract (`CONTRACTS.md`), `pathfinder_ml` loader, pipeline |
| `snapshots/` | Committed artefacts the app loads: `ml/` (Arsenii), `catalogue.json`, `routes.json`, mocks |

## Getting the data

```bash
pip install -r requirements-data.txt
cp .env.example .env          # Adzuna keys, cluster alias
make data-dry                 # see what will be fetched
make data                     # ONS crosswalks, ASHE 2011-2025, Nomis dataset definitions
# browser downloads: ESCO, ILO WP140, Occupations in Demand (see data/manifest.yaml)
make data-check               # what is present, checksums
make data-sync                # rsync data/raw to the cluster
make adzuna                   # laptop only: dated Adzuna snapshot
```

## Running

`docker compose up` (to be added by the backend slice). The demo must work with no API keys.

## Sources and attribution

Jobs by Adzuna; ONS (Open Government Licence); Skills England / DfE (OGL); ILO Working Paper 140
(Gmyrek et al., 2025); ESCO (European Commission); HESA / Discover Uni (CC BY 4.0).

## AI use

To be completed: where the app uses AI, what stays human, and which coding agents built it.
