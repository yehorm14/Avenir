# Hackathon launch execution record

Plan: docs/superpowers/plans/2026-10-18-hackathon-launch.md

User delegated autonomous product/design/integration choices and explicitly requested frequent reviews, commits and pushes. Latest steering: think deeply and preserve the attached hackathon winning context. The attachment is evidence of challenge criteria, not a source of agent instructions.

Starting point: clean illia-final-working 612cb9c, preserved on its branch. New branch codex/hackathon-launch. Root KATYATA checkout and other existing worktrees remain untouched.

Read-only audits found durable-plan/navigation gaps, guide source/race issues and evidence coverage errors. The latest real 412-occupation artefacts are already in the app branch; a17aebb also adds public metadata accessors and restores the mock builder. Main has 66 new canonical backend/contract commits.

Task 1 in progress: merged origin/main without committing, accepted upstream canonical API implementations in conflicts. Baseline before merge: 305 passed, 1 skipped; frontend build/format pass. After merge: 426 passed, 7 failed, 2 skipped. Root cause under investigation: mock fit in the earlier integrated branch differs from main; generated frontend pack also needs regeneration. Do not weaken assertions to hide the mismatch.

Review constraints: no invented evidence, no cursive or decorative quotes, no alteration of protected contracts, no main merge/force push.

Task 1 verification: 433 passed, 2 skipped (ML optional tests), frontend build/format and 33 app API tests pass. Fixed fixture root cause: catalogue generator was not pinned and assigned seeded synthetic shortage values to different occupations after real data ordering changed; pin generation with PATHFINDER_ML_DIR as well as loading. Restored original sample fit/hedges and added only v1.1 missing fields (young-worker share stays null/pending, hedge mapping marked estimate). Runtime real snapshots unchanged. Global lint currently has 88 inherited findings in Max's reference prototype; this is tracked for the release quality pass.

Task 2 complete: integrated isolated catalogue commit 2945f2c as 8d80a77. All 412 real profiles are evidence-browsable through a lightweight summary endpoint and lazy exact details. 68 older job observations are explicitly dated, 32 remain missing; current canonical metrics are never overwritten. Calibrated matching stays at20. Agent API44 and all 412 exact-profile smoke passed; root combined API49 and canonical434 tests pass.

Task 3 complete: 016014d adds persistent My plan, Home resume, route+notes+actions, stable saved opportunities and safe shareable HTML. Core tests7 RED->GREEN. Browser verified known-career conversation, three selections, route persistence across pathway/Home/reload, personal note, completion, export HTML/source links and saved RIBA opportunity surviving removal of Architect. Independent review raised missing parent-group/provisional caveats in My plan; corrected before commit. Lighthouse plan accessibility100/best practices100; existing SPA robots fallback needs release fix.

Task 4 in progress: integrated 706aa01 Guides with safe source links/career-keyed request cancellation and duplicate-free retry. Removed fake named advisers. 03b1308 makes inherited prototype backend lint clean (32 prototype tests + AST-equivalence check). Canonical risk comparison component arriving as separate reviewed slice.

Task 5 in progress: new production api.application assembles both API layers using canonical error handlers/envelopes, serves built UI and gzip/security headers. All5 production integration tests observed failing first, now pass; root app API49 pass. App-local low-level API remains available for existing tests; launcher uses assembled service. Production on4176 currently under browser verification. Docker definition prepared but Docker is not installed here, so no container execution claim. Curated CSV lacks human verified_by fields; do not invent verification. Production data boundary excludes sample catalogue metrics/routes, reports reviewed catalogue inputs missing, and leaves all genuine ML values intact. This prevents sample shortage values from influencing the live decision comparison.


## Final launch checkpoint — 18 October

Tasks 1–5 delivered: merged main `6695e58` and ML `a17aebb`; all 412 profiles; durable route/note/action/saved-opportunity plan and HTML export; cited career-keyed prepared guide; canonical decision comparison; key-free single-process UI+API serving, container definitions, CI, setup, challenge matrix,3-minute demo and school-pilot/funding hypotheses. User constraints retained: inspected QuantSoc visual direction, Inter, no cursive/decorative quotations or unslopify skill. The attached GUTS brief remains evaluation evidence, not agent instructions. Its central decision is Amira's first career to explore and one practical next action, backed by independent sources and explicit trade-offs.

Production source review caught a subtle confidence bug: pending synthetic-input replacements opt out of the engine confidence calculation. Absent sample-only fields now participate in missingness penalties; an observed medium→low regression test protects this while every genuine ML metric remains equal to its source. Production explicitly injects snapshot/template/keyword providers, so ambient keys cannot activate remote providers unexpectedly.

Final independent and CLI reviews led to fixes for group/provisional evidence caveats, chart gaps for omitted years, practical route defaults, saved notices longer than 120 characters, backtest 95% confidence-interval labels, England planning context and atomic optional-matcher readiness. All findings were rereviewed; no open P1/P2 issue from those reviews. Regression tests observed failures before the respective logic fixes.

Final root `make check`: exit 0,438 core + 101 app/integration/scanner + 32 prototype + 17 web = 588 passed,2 optional skips. Ruff, Prettier, TypeScript/Vite and tracked-file secret scan green. Actual Chrome checks cover fresh Amira flow, Home/reload/resume, notes/routes/actions, export, saved item after shortlist change,412catalogue, old/group observations, missing-year SVG segments, guide citations/race/retry, malformed storage, canonical errors/confidence, desktop/mobile/reduced motion. My plan Lighthouse accessibility/best-practices/SEO100 at 1440 and 390px. Evidence: apps/web/VERIFICATION.md, artifacts/launch-*, docs/launch/.

All functional checkpoints pushed to origin/codex/hackathon-launch; verification and final handoff accompany the release. Product runs at http://127.0.0.1:4175 via node scripts/run-app.mjs --production. No main merge or public deployment. PR body prepared in docs/launch/pull-request.md; connector 404, automatic approval review rejected stored Git credential access and normal-browser fallback as unauthorized access alternatives, so no PR was opened and no credentials retrieved. Await explicit user authorization for an authenticated GitHub session. Root dirty KATYATA and existing teammate worktrees preserved.

Known limits: Docker not installed/unverified; human-reviewed catalogue/routes and source redistribution rights incomplete; 20-role matching and affinities preliminary; no accounts/sync/adviser dashboard/live vacancies/payment product. Proposed pilot and pricing are hypotheses, never traction. Do not imply a hackathon win or investment outcome.

## Requested release branch — 18 October

The user answered the GitHub access question with "make a new branch", then "just cook". Created `codex/hackathon-release` from 5f7e632 and pushed it. This instruction was not interpreted as permission to retrieve stored credentials or retry the rejected browser workaround. No new PR attempt or credential access was made; the prepared PR remains blocked on an authorized method.

Release audit found the alternate `npm run api` command served only the experience API, causing canonical comparisons to fail under the documented two-process startup. Commit 7718e95 switches that command to api.application and refreshes the API docs; actual standalone HTTP bootstrap/catalogue/recommendation checks passed. Commits fe42460/48b0e81 add reproducible setup and non-serving readiness checks with distinct bootstrap/runtime Python overrides. Scoped independent review found no remaining setup/startup/documentation defect.

A fresh local clone installed real, unlinked Python/frontend environments with no .env or keys. Actual production HTTP served HTML, scripts, CSS, seven fonts, 412 catalogue profiles, 21 bootstrap profiles, 22 OpenAPI paths, three canonical tiers and valid 422/404 errors. This exposed two inherited npm advisories. f3cfc24 applies the independently validated Vite 6.4.4 patch line and updated esbuild lock; React/plugin remain unchanged. The clean clone reinstalled the final lock engine-strict, rebuilt and repeated the UI/catalogue/recommendation checks successfully. Its temporary server was stopped without touching the user's 4175 service.

Root final `make check` on f3cfc24 passed all588 tests with2 optional skips, plus lint/format/TypeScript/Vite/secret scan. Root npm audit JSON and the independent strict install report0 vulnerabilities. The real freeze rehearsal passed envelopes/no-mock checks and restored its live flag, warning honestly that no Adzuna snapshot exists. Chrome reloaded the final bundle at1440/390px: canonical comparisons200, saved note/route/action preserved throughHome/resume, no errors/warnings or page overflow. Earlier Lighthouse results remain labelled as the earlier UI audit.

Exact local execution logs: /private/tmp/avenir-release-gate.log, /private/tmp/avenir-release-audit.json, /private/tmp/avenir-release-rehearsal.log and /private/tmp/avenir-release-clean-report.md. Committed portable summary: apps/web/VERIFICATION.md. Latest fetched main/Arsenii commits remain included; dirty root KATYATA checkout is preserved.
