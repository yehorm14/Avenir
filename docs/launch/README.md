# Aventier launch handoff

Aventier helps a school leaver compare career directions, choose a first route to explore and leave with a practical plan. The demo follows Amira, 17, in Glasgow: she enjoys maths and art, starts with architecture and wants to understand the trade-offs before committing.

The challenge is **ONE APP ONE CLEAR DECISION**. The decision is which career to explore first and what to do next. The product makes the evidence, uncertainty and alternative routes visible while the learner keeps control.

- [Three-minute demo script](demo-script.md)
- [Business and pilot hypotheses](business-case.md)
- [Application setup](../../apps/web/README.md), [API contract](../contracts.md), [ML contract](../../packages/ml/CONTRACTS.md), [source registry](../../snapshots/ml/sources.json) and [data manifest](../../data/manifest.yaml)

## Demo scope and claim boundaries

| Available in the launch flow                                                                     | Boundary to state clearly                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Known-direction or exploring conversation; three weighted career options; learner-ranked choices | Interest matching covers 20 roles. Its embedding affinities are preliminary; development labels are synthetic. No validated matching-accuracy claim is made.                                                                          |
| Jobs evidence catalogue with 412 occupation profiles                                             | This is evidence coverage, not 412 calibrated recommendations or 412 detailed training plans. The supplied snapshot has 409 median-pay values and 409 demand-trend values; individual metrics and histories may still be unavailable. |
| Persistent My plan with route, note, next actions, saved opportunities and export                | Progress is stored in this browser. There are no accounts, cross-device sync or adviser dashboards in the demo.                                                                                                                       |
| Pay, employment, automation research, return/risk comparison and historical backtest             | Median workforce pay is not starting pay. Employment trends are historical. Exposure is not a job-loss probability. Return/risk values are comparison indices, not personal earnings forecasts.                                       |
| Prepared career guide with source links; curated study and opportunity links                     | No live conversational AI or live vacancies are promised. Course eligibility, openings, dates and costs must be checked with the original provider.                                                                                   |

## Three layers and independent evidence

The [React UI](../../apps/web/src/) owns discovery, comparison, the saved plan and accessible evidence views. The [decision package](../../packages/decision/) owns deterministic fit, return/risk components, alternatives and roadmap rules; [app ranking](../../apps/web/api/ranking.py) applies the learner's pay, interest and observed-demand priorities. The [API boundary](../../apps/web/api/) joins these to the [canonical API](../../services/api/), [provider adapters](../../packages/adapters/) and [committed ML snapshots](../../snapshots/ml/). Decision functions perform no network calls and do not ask a language model to rank careers.

ONS ASHE supplies earnings and employee-job observations; ILO Working Paper 140 supplies an independent automation-exposure research perspective. ONS CPIH supplies inflation adjustment. Skills England demand assessments and ESCO skill relationships add further context where available. Preserve each source's period, geography, granularity, confidence and licence notes. Combining indicators does not remove their limitations or make them statistically independent.

## Run and verify

From the repository root, with Node 20+ and Python 3.12+:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/web ci
node scripts/run-app.mjs
```

Open [the local app](http://127.0.0.1:4175). No API key is required. For the existing built-preview launcher:

```sh
npm --prefix apps/web run build
node scripts/run-app.mjs --preview
```

The release owner must confirm the final same-origin production startup and port when integrating the container. The [Compose configuration](../../docker-compose.yml) must start the complete UI/API stack with empty optional provider credentials before one-command deployment is claimed:

```sh
docker compose up --build
```

Run these checks against the final integrated commit; record actual output, skipped checks, browser evidence and any unresolved failures. This document does not certify a pass or give a test count.

```sh
npm --prefix apps/web run format:check
npm --prefix apps/web run build
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest apps/web/api/tests -q
gitleaks detect --no-banner --redact
```

The secret scan requires `gitleaks` to be installed. A missing scanner is an uncompleted check.

## Challenge acceptance matrix

| Requirement                                        | Repository evidence                                                                                                                           | Release verification                                                                                                                                                                                                                             |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| One coherent decision                              | [App flow](../../apps/web/src/App.tsx), [discovery](../../apps/web/src/Discovery.tsx)                                                         | Follow Amira from Home to ranked choices, a chosen route and one concrete next action. Return Home and resume My plan.                                                                                                                           |
| Two or more independent sources                    | [Source registry](../../snapshots/ml/sources.json), [data notes](../data-sources.md)                                                          | Inspect an ONS pay statistic and an ILO exposure estimate. Show dates, coverage and caveats beside the numbers.                                                                                                                                  |
| API-first interface, envelopes, errors and OpenAPI | [Contracts](../contracts.md), [canonical API](../../services/api/), [app API](../../apps/web/api/)                                            | Inspect OpenAPI; exercise success, malformed input, unknown occupation and missing-provider paths. Confirm consistent error shape and source metadata at the served boundary.                                                                    |
| UI, decision and provider separation               | [UI](../../apps/web/src/), [pure decision layer](../../packages/decision/), [adapters](../../packages/adapters/)                              | Trace one recommendation from request to pure scoring to loaded provider evidence. Confirm no credentials or provider calls in browser code.                                                                                                     |
| Core unit and integration tests                    | [Decision tests](../../packages/decision/tests/), [API tests](../../services/api/tests/), [app tests](../../apps/web/api/tests/)              | Run both pytest commands above. Include missing values, weights, distinct choices, validation, source preservation and end-to-end API joining.                                                                                                   |
| Resilience and honest missing values               | [ML loader](../../packages/ml/pathfinder_ml/), [guide UI](../../apps/web/src/Guides.tsx), [API](../../apps/web/api/)                          | Keep local servers running, disconnect external internet and repeat the flow. Confirm prepared guidance still works, missing evidence stays missing and failed requests offer retry. Never relabel sample fallback data as real.                 |
| Reproducible setup and no secrets                  | [App setup](../../apps/web/README.md), [environment example](../../.env.example), [Compose](../../docker-compose.yml)                         | Start from a clean checkout, empty optional credentials and committed snapshots. Build the production stack and run the secret scan.                                                                                                             |
| Accessible, cohesive experience                    | [Styles](../../apps/web/src/styles.css), [charts](../../apps/web/src/Charts.tsx), [guide](../../apps/web/src/Guides.tsx)                      | Use keyboard only through discovery, ranking, plan, chart inspection and modal close. Check readable focus, reduced motion, narrow viewport and text alternatives to charts.                                                                     |
| Responsible AI with checks and fallback            | [ML method and evaluation](../../packages/ml/README.md), [guide](../../apps/web/src/Guides.tsx), [adapter boundary](../../packages/adapters/) | Explain preliminary affinities and synthetic development labels. Show deterministic ranking and prepared cited replies without a live model. Any optional generated explanation must preserve source facts and caveats, with an honest fallback. |
| Honest historical evaluation                       | [Backtest artefact](../../snapshots/ml/backtest.json), [ML tests](../../packages/ml/tests/)                                                   | Show a negative result and the documented windows, overlapping samples and 2021 coding break. Confirm time-split checks run; do not present this as validation of personalised matching.                                                         |

Public release also needs the unresolved licence entries in the source registry resolved or the affected content excluded. The demo's attribution and provenance are a starting point for that review, not permission to redistribute every source.
