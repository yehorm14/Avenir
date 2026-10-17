# Backend split: Yehor and Nazar

*Sat 17 Oct, 20:50. Freeze Sun 11:30.*

## The seam

```
 Arsenii ─► packages/ml (pathfinder_ml) ─► snapshots/ml/*.json   (pay, demand, exposure, resilience,
                                                                  history, hedges, fit, backtest, crises, sources)
 Yehor   ─► avenir_etl ─► snapshots/catalogue.json, routes.json  (titles, aliases, entry subjects, shortage,
                                                                  wellbeing, stress, Scottish routes)
                   │
         avenir_contracts.load_data()  ──►  AvenirData (20 joined Careers + everything else)
                   │
 Nazar   ─► avenir_decision.recommend() ◄── avenir_api (FastAPI) ─► docs/openapi.json ─► frontend
                                                 ▲
 Yehor   ─► avenir_adapters.registry: ads_source(), explanation_writer(), tag_suggester()
```

Everything between slices goes through `packages/ml/CONTRACTS.md` (Arsenii) and
`packages/contracts/avenir_contracts/` (Yehor). Until real files land, everything runs on
`snapshots/ml/mock/` (many values already real, preliminary) and `snapshots/mock/`.

## Who owns what

| | Yehor | Nazar |
| --- | --- | --- |
| Plan | `docs/superpowers/plans/2026-10-17-avenir-data-and-adapters.md` | `docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md` |
| Folders | `packages/contracts`, `packages/adapters`, `packages/etl`, `scripts/fetch`, `data/` | `packages/decision`, `services/api`, `docker-compose.yml`, `docs/openapi.json` |
| Branches | `yehor/<topic>` | `nazar/decision`, `nazar/api` |
| Context file | `context/yehor-backend.md` | `context/nazar-backend.md` |
| Delivers | real `catalogue.json`, `routes.json`; live adapters | `recommend()`; all 14 endpoints; Docker; OpenAPI for the frontend |

## Timeline

| When | Yehor | Nazar |
| --- | --- | --- |
| 20:50-21:00 | Merge contract PR to `main` | Read AGENTS.md, spec, contract code, his plan |
| 21:00-23:00 | Tasks 1-3 (registry, Adzuna, LLM); team fills `data/curated/occupations.csv` | Track A Tasks 1-6 and Track B Tasks 11-12 in parallel |
| 23:00-01:00 | Tasks 4-6 (catalogue, shortage, Scottish routes) | Track A Tasks 7-10, PR; then Task 13 |
| 01:00 | **Checkpoint:** API serves the Amira flow on mock data; frontend points at it | |
| Sun 08:00-10:00 | Real catalogue and routes; Arsenii's real artefacts land in `snapshots/ml/` | Tasks 14-15; fix integration issues |
| 10:00-11:30 | Run with `AVENIR_FREEZE=1`; README sections | Same; rehearsal support |

## Rules for changing the seam

- A contract change is a PR to `packages/contracts` with "needs a contract change" ticked, reviewed by both of us. Regenerate `snapshots/mock/` (`python -m avenir_contracts.mock`) and `docs/openapi.json` in the same PR.
- If a plan rule turns out wrong (a weight, a threshold), change it in your own package and note it in your context file; don't wait.
- Ask each other in the PR, not in chat, so the agents can see the answer.
