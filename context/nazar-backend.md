# Nazar: backend (decision engine + API)

- **Owner:** Nazar (human) / Claude (orchestrator) with Haiku and Sonnet subagents
- **Branches:** `nazar/decision` (Track A), `nazar/api` (Track B), both on `main` 227b5e9 (contract v2)
- **PR:** #8 (decision, Tasks 1-10) and #9 (api, Tasks 11-15, built on top of #8), drafts
- **Status:** ready for review — all 15 plan tasks done; each task reviewed; final whole-branch review of the decision engine done and its fixes re-reviewed

## Task
Build `packages/decision` (pure scoring: picks, hedge, roadmap, notices, `recommend()`) and
`services/api` (FastAPI, envelope, all endpoints, OpenAPI, Docker), following
`docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md` (v2).

## Done so far
| Task | Branch | What |
| --- | --- | --- |
| 1 ranks | decision | `rank_0_100`; fixtures load mocks via `load_data` |
| 2 confidence | decision | `lowest`, `downgrade`, `component_confidence` |
| 3 fit | decision | `fit_scores`, `head_start`; Amira: Architect 58.3 best |
| 4 components | decision | return, market risk, disruption risk, risk (slider) |
| 5 picks | decision | Amira (first idea Architect excluded): 7 eligible; ambitious 2141 Web designer, safe 2452 Architectural technologist or planner, balanced 2453 Quantity surveyor |
| 6 first idea + compare | decision | `resolve_first_idea`, `first_idea_candidates`, `vs_first_idea` |
| 7 hedge | decision | `choose_hedge`; Amira's top pick 2141 → hedge 2123 Electrical engineer (risk −12.3) |
| 8 roadmap | decision | `build_roadmap`; Amira / 2141: "Take Higher Computing", graduate apprenticeship route, milestone, this month |
| 9 reasons + notices | decision | template sentences from the numbers only; MUST_MENTION flags → `notices` |
| 10 `recommend()` | decision | one entry point; fills `first_idea_candidates` and hedge `evidence` when the contract has them (v2.1) |
| final fixes | decision | first idea matches whole words only (≥ 3 letters): "IT", "art", "x" no longer resolve; junk from the explanation writer falls back to the template |
| 13 write endpoints | api | `/profile`, `/recommendations`, `/careers/{soc}/hedge`, `/demo/live` (pull the plug); unknown tag → 422 naming it; no data → 503 |
| 14 OpenAPI + Docker | api | `docs/openapi.json` (+ freshness test), `services/api/Dockerfile`, `docker-compose.yml`, `make run`, `make openapi` |
| 15 provenance + freeze | api | every metric in a recommendation has source/confidence/status/flags; `AVENIR_FREEZE=1` fails while catalogue/routes are mock |
| 11 app, envelope, errors | api | `create_app(data)`, `/health` with `ml_mode`; runs with no keys, no data dirs |
| 12 read endpoints | api | tags, sources, careers, career card (+ads overlay), history, crises, backtest(+years), routes |

Each task: tests first, implemented by a subagent, reviewed against the plan by a separate
reviewer, checked by the orchestrator. One commit per task.

## Decisions (Nazar, 17 Oct)
1. Fit gate (Task 5): best fit is taken among careers other than the first idea (plan rule); the
   plan's "6 eligible" note was a typo, Amira gets 7.
2. Backtest (Task 12): any `/api/v1/backtest` request with no backtest data loaded → 503
   `UPSTREAM_UNAVAILABLE`; 404 only for a year missing from loaded data.
3. Pending metrics (Task 4): metrics with `status: "pending"` (source not loaded yet) are skipped in
   scores and do not lower confidence; only career-specific gaps do.
4. `exposure_uk` (Task 4) is a cross-check only, not a confidence input.
5. First idea (Task 6): never guess. A tie between distinct careers at any matching step (exact
   name, contains, fuzzy) → `first_idea: null` plus candidates; e.g. "engineer" → Civil engineer
   (2121) and Electrical engineer (2123).
6. Candidates in the API need a contract field: proposed to Yehor as
   `RecommendationOut.first_idea_candidates: list[CareerRef{soc2020, title}]`. Until it lands,
   ambiguous text gives `first_idea: null` only.
7. Task 14 may add only `run` and `openapi` targets to `Makefile`.
8. Sync: before every task, fetch, rebase on `main`, read and test against `yehor/*` branches
   (never merge them into ours).
9. Hedge ties (Task 7): highest similarity → lower risk → higher fit → lower SOC.
10. Roadmap (Task 8): Higher, Advanced Higher and A-level count as "held"; GCSE / National 5 don't.
11. Reasons (Task 9, next): a source not in `SOURCE_LABELS` shows its raw id; a metric with no
    year drops just the year.
12. Contract v2.1 (PR #4): acked by Nazar. Yehor added `first_idea_candidates` (as proposed); `recommend()`
    fills it and hedge `evidence` when present (tested against #4 in a scratch merge).
13. (Orchestrator, Nazar said "don't ask, finish") `nazar/api` is built on top of `nazar/decision` instead of
    waiting for #8 to merge; after #8 squash-merges: `git rebase --onto origin/main <decision tip> nazar/api`.
14. (Orchestrator) first-idea "contains" matching needs a word start and ≥ 3 letters (final review: "IT" →
    Architect was a guess). Still by plan rule: "maths" → Secondary school teacher (alias "maths teacher"),
    "developer" → Web designer (alias "web developer").
15. (Orchestrator) the standalone hedge endpoint also shows live `ads_now`, like the hedge in recommendations.

## For Arsenii
- Pick rules (Task 5) his backtest groups should use: eligible = fit ≥ max(5, 0.5 × best fit among
  non-excluded careers) with return and risk present; ambitious = max return; safe = min risk of the
  rest; balanced = max (return − 50) / max(risk, 10) of the rest; ties: higher fit, then lower SOC.

## Deferred minor findings (for the final review)
- API: non-404 HTTP errors (e.g. 405) map to 500; unhandled 500s lack CORS headers; error
  envelopes have empty `meta.sources`.
- Decision: no NaN guard in ranks; double rounding in risk; a short alias inside longer typed text
  can match (plan rule, e.g. "technician"); several coverage gaps noted per task.
- Repo: `ruff format --check` fails on several files (mostly contract files); not in `make check`.

## Blocked on
- Nothing in code. Merge order: #4 (contract v2.1) → #8 → rebase #9 → #9.
- `docker compose up` not run: Docker isn't installed on Nazar's Mac (pip-install simulation passed).
- Freeze test fails until real `snapshots/catalogue.json` and `routes.json` land (Yehor, Sun 08:00).

## For Arsenii (also)
- `pathfinder_ml` mock fallback dir is fixed relative to its install path; the Dockerfile symlinks it.
  An env var (e.g. `PATHFINDER_ML_MOCK_DIR`) would be cleaner.

## Open questions (for humans)
- Roadmap step 1 says "Take Higher ..." for every nation (plan rule); English students see it too.

## Marked (verify)
- None.

## Next step
Yehor reviews #8 then #9. After #4 merges: rebase both, drop the feature detection if wanted.
Sun 08:00-10:00: real catalogue/routes/ML land → run `AVENIR_FREEZE=1 pytest` and fix what breaks.
