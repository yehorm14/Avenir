# Avenir

A career decision tool for UK school leavers: it compares Computer Science and Finance careers using real UK pay, employment and automation data, then builds a plan.

![Avenir home screen](docs/images/home.png)

## Why it is useful

- Every pay and job figure shows its ONS source, year and caveats.
- Automation exposure sits next to pay and job trend, labelled as research, not a job-loss forecast.
- The outcome is a saved plan with a route and next actions, not a score.

## Features

- Evidence dashboards for Computer Science and Finance: pay history, jobs, 2022-2025 trend, automation exposure, starting-pay guides.
- Compare tab that weighs pay against employment trend and suggests a first role.
- My plan: route, reasons and actions saved in the browser, downloadable as HTML.
- Jobs directory of 412 occupation profiles and a quiz matching interests to 20 roles.
- Career chatbot answering from the app's data, with sources.
- Historical backtest of simple rules, including failed checks.
- Pull-the-plug harness that disables live sources to show the snapshot fallback.

## How it works

One FastAPI process serves the React app and the APIs, all using an `{ok, data, error, meta}` envelope with source status.
Decision rules are plain functions in `packages/decision`; no LLM ranks careers.
The app serves committed ONS, ILO and ESCO snapshots. Adzuna and LLM adapters (`packages/adapters`) have timeouts and snapshot or template fallbacks.
The chatbot uses an LLM only if a key is configured, and checks its numbers against the sources.

## Tech stack

- Backend: Python 3.12+, FastAPI, Pydantic
- Frontend: React, TypeScript, Vite
- Data: JSON snapshots (ONS ASHE, CPIH, ILO WP140, ESCO), CSV curation
- Tooling: pytest, Ruff, Prettier, Node test runner, GitHub Actions, Docker

## Run locally

```sh
bash scripts/setup.sh
node scripts/run-app.mjs --production   # http://127.0.0.1:4175
```

Needs Python 3.12+ and Node 20+. No keys required; optional settings are in `.env.example`. Docker and Render: [docs/DEPLOY.md](docs/DEPLOY.md).

## Tests

686 Python tests and 55 Node tests: `make check` (also runs lint, build and a secret scan; CI runs the same).

## Team and my role

Built at GUTS 2026 for the BlackRock challenge with [iluha2vuha](https://github.com/iluha2vuha), [Nazar818](https://github.com/Nazar818), [z1nare](https://github.com/z1nare) and [maksymkhomitskyi](https://github.com/maksymkhomitskyi). I was the integrator and built:

- the API contract (`packages/contracts`)
- the ETL and data pipeline (`packages/etl`)
- the live adapters: Adzuna with snapshot fallback, and LLM explanations (`packages/adapters`)

## Credits

Data: ONS ASHE and CPIH (Open Government Licence); Skills England / DfE (OGL); ESCO (European Commission); HESA / Discover Uni (CC BY 4.0); ILO Working Paper 140, Gmyrek et al., 2025 (CC BY 4.0). Ads: Jobs by Adzuna. Details: [docs/data-sources.md](docs/data-sources.md).

> This is an adaptation of a copyrighted work of the International Labour Organization (ILO). This adaptation has not been prepared, reviewed or endorsed by the ILO and should not be considered an official ILO adaptation. The ILO disclaims all responsibility for its content and accuracy.
