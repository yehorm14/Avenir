# yehor: backend (contract, catalogue, routes, live adapters)

- **Owner:** Yehor (human) / Claude (agents); Codex runs the integration harness
- **Status:** backend merged to `main` (Sun 18 Oct, ~00:20). Only verification and Sunday's real-data steps remain.

## On main
| PR | What |
| --- | --- |
| #4 | Contract v2.1: ML v1.1 fields, `first_idea_candidates`, malformed SOC 422, 5 MB rule for `snapshots/ml` |
| #5 | Live adapters: registry, Adzuna (hard 3 s, breaker, snapshot fallback), LLM explanation (checked, template fallback) |
| #3 | Catalogue + routes build (`python -m avenir_etl.build`); manifest gains Arsenii's 8 sources (URLs and licences marked verify) |
| #6, #15 | Frontend pack: `docs/frontend/` README, schemas, examples, matched to the live API |
| #11 | Pull-the-plug demo harness: `python scripts/demo/pull_the_plug.py` |
| #12, #13 | Team plans: `docs/updates/2026-10-18-frontend-plan.md`, `docs/updates/2026-10-18-ml-pipeline-plan.md` |
| Nazar #8, #9, #14 | Decision engine, API, follow-ups (nation roadmap wording, longest alias, 422, parallel ads) |

`main`: 416 passed, 1 skipped, ruff clean. `AVENIR_FREEZE=1`: only `test_no_mock_at_freeze` fails (sample data, by design until Sunday).
The repo is squash-merge only from now on; merged and stale branches are deleted.

## Verified tonight
- A fresh install, every endpoint, error codes, the Amira flows ("architect", "engineer", "astronaut") and the demo harness all pass; responses take 3-65 ms.
- Rehearsal of Sunday's catalogue build (temp copy, `verified_by` filled): catalogue/routes become `preliminary`.
- Rehearsal with Arsenii's real v1.1 overlaid: real numbers on every card, no errors; picks Web designer / Civil engineer / Quantity surveyor, hedge Graphic designer.
- Frontend: every live response validates against `docs/frontend/schemas`; TypeScript types from `docs/openapi.json` pass `tsc --strict`.

## Sunday
1. 08:00: team fills `verified_by` + descriptions in `data/curated/occupations.csv` and real routes in `routes.csv` (CSV UTF-8).
2. Arsenii's real data PR #16 (opened early): Codex checks it; merge when green.
3. ~09:30: `python -m avenir_etl.build`, commit `snapshots/catalogue.json` + `routes.json`; `python -m avenir_contracts.examples` to regenerate the frontend pack.
4. 10:00: `AVENIR_FREEZE=1 pytest` green (except `ml_fit` if the matcher misses); rehearse with the demo harness.

## Open decisions
- Pull the plug: switch off the matcher + LLM too (today only Adzuna, which has no key, so nothing visible changes).
- BGE matcher in Avenir: needs Arsenii's service + a small adapter from me; otherwise the pitch says "keyword matching today".
- GDELT "news attention": decide at 01:00, only if the frontend is on track.
- F06: sibling-mean exposure must stay missing (AGENTS rule 3); F01 backtest look-ahead for Arsenii.

## Blocked on (humans)
- Adzuna keys (optional now); LLM key (optional); OiD download (shortage flag).
- Licence checks (`licence_checked_by` is empty everywhere); manifest URLs.
- Maksym: 2 possible keys in `Advisers.tsx` (prototype branch).
- Start Docker Desktop once to test `docker compose up`.

## Marked (verify)
- Manifest: 7 empty URLs, the ASHE 2007-10 page, all licences. ELM/Gemini API shape. Occupations in Demand labels.
