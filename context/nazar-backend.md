# Nazar: backend (decision engine + API)

- **Owner:** Nazar (human) / Claude (orchestrator) with Haiku and Sonnet subagents
- **Branches:** `nazar/decision` (Track A), `nazar/api` (Track B), both rebased on `main` 227b5e9 (contract v2)
- **PR:** none yet (draft PRs at checkpoint 1)
- **Status:** in progress (Tasks 1 and 11 done, plan v2)

## Task
Build `packages/decision` (pure scoring: picks, hedge, roadmap, notices, `recommend()`) and
`services/api` (FastAPI, envelope, all endpoints, OpenAPI, Docker), following
`docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md` (v2).

## Done so far
| Task | Branch | Commit | Notes |
| --- | --- | --- | --- |
| 1 ranks + test fixtures | `nazar/decision` | `feat(decision): 0-100 ranks with ties and missing values` | fixtures use `load_data(snapshot_dir=tmp)` after `mock.write(tmp/"mock")` |
| 11 app, envelope, errors | `nazar/api` | `feat(api): app, envelope and error handling` | `create_app(data: AvenirData)`, `/health` reports `ml_mode`; starts with no keys and no data dirs |

Each task: tests written first, implemented by a subagent, reviewed against the plan by a
separate reviewer, then checked by the orchestrator. Rebased onto contract v2 on 17 Oct and
amended (one commit per task).

## Execution plan
| Phase | Track | Tasks | Done when |
| --- | --- | --- | --- |
| 1 | A / B | 1 ✅, 2 confidence / 11 ✅ | plan tests pass |
| 2 | A / B | 3 fit, 4 components, 5 picks, 6 first idea / 12 read endpoints | Review Focus 1-4 tested |
| CP1 | | draft PRs "nazar: decision engine", "nazar: API skeleton" | tell Nazar |
| 3 | A | 7 hedge, 8 roadmap, 9 reasons + notices, 10 `recommend()` | PR ready for review |
| 4 | B | rebase on `main` after Track A merge; 13 write endpoints; 14 OpenAPI + Docker | Review Focus 5 tested |
| CP3 01:00 | B | uvicorn serves the Amira flow on mock data; `docs/openapi.json` to frontend | |
| 5 Sun 08-10 | B | real `snapshots/ml/*.json` + catalogue; 15 provenance + freeze tests | `AVENIR_FREEZE=1` green |

## Decisions
- Branches started from Yehor's contract branch, now rebased on `main` (contract v2).
- Task 14 may add only `run` and `openapi` targets to `Makefile` (Nazar approved, 17 Oct).
- Task 13's empty `first_idea` test must send a valid profile, or the first error is the missing profile.

## Deferred minor findings (for the final review)
- API: non-404 HTTP errors (e.g. 405) map to 500; unhandled 500s lack CORS headers; no test for
  the `default_ports()` ImportError fallback or `X-Request-ID` on success.
- Decision: `rank_0_100` does not guard NaN; more rank edge-case tests possible.
- Repo: `ruff format --check` fails on several files (mostly contract files); not part of `make check`.

## Blocked on
- Task 13 needs Track A merged into `main`.

## Open questions (for humans)
- Roadmap step 1 says "Take Higher ..." for every nation (plan rule); English students would see it too.

## Marked (verify)
- None yet.

## Next step
Task 2 (confidence, Track A) and Task 12 (read endpoints, Track B).
