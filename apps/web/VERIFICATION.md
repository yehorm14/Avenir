# Final CS/Finance delivery verification — 18 October 2026

Current local branch: `codex/final-delivery`. Runtime checkpoint: `538690c` (final follow-up increases historical-stat readability and records verification). Preview: http://127.0.0.1:4186. The previous 4175 release and original dirty checkout are preserved. This delivery is committed locally; it has not been pushed, merged or publicly deployed.

## Current release gate

`PATH="$PWD/.venv/bin:$PATH" make check` passed: **645 tests passed, 3 optional tests skipped** — 467 core, 120 app/API/integration/scripts, 32 preserved prototype and 26 web tests. Repository Ruff, frontend formatting, TypeScript/Vite production build and tracked-file secret scan passed. The final CTA, keyboard-focus and method-wording refinements were followed by fresh web tests, formatting and production build. The scan checks current tracked files, not all history or untracked files.

ML owner release v1.2 was integrated atomically with authorship retained. The UI/API carry its tax-year price metadata, multiplicative relative employment trend and uncertainty flags. Low-purity historical pay mappings break at 2021. Both failed-placebo crisis metrics are excluded at the production decision-input boundary; raw evidence is preserved. Fixture assertions were updated to exact owner outputs, and the narrow-profile API test retains controlled eligibility rather than accepting extra recommendations.

## Current browser evidence

Three independent specialists and the integrator exercised the built UI against the assembled service in isolated browser contexts at **1200×800 and 1440×1000**:

- All seven scoped roles open directly with correct hash, title, evidence and sources. Rapid changes, Back/Forward and reload preserve role consistency. Both chart price bases and relative trend periods match the v1.2 API.
- Compare stays within four CS or three Finance roles. Actual rows and comparison indices match the API. CS pay priority selects IT business analyst; balanced/trend selects Cyber security. The Finance grouped role leads all three presets in this snapshot; no artificial movement is added.
- Exactly one Build my plan action is shown in Compare. The chosen role and actual pay/trend weights reach the plan and export without inventing interest matching or quiz completion. Explore returns keyboard focus to the persistent Evidence button.
- Route, personal note, completed action and saved opportunity survive reload and export. Export escapes markup and retains source links and actual data periods. Career-scoped guides do not mutate the plan; the grouped Finance guide does not borrow software-entry advice.
- Simulated comparison failures remove stale recommendations; Retry recovers and delayed aborted responses cannot overwrite newer priorities. Bootstrap failure recovers through Try again. Offline guide failure retries without duplicating a question.
- No page overflow, clipped controls, console warnings or console errors in the audited flows. Path route selector and guide Send control are visible at 1200×800. Lower table rows and detailed caveats use ordinary vertical scrolling.

Lighthouse snapshot audits on current CS/Finance Evidence and Compare views scored **100 accessibility, 100 best practices, 100 SEO and 100 agentic browsing**, with zero failed audits. These exclude performance and do not certify every assistive technology or route. [Compact audit record](artifacts/final-browser-audit.json), [CS screenshot](artifacts/demo-cs-desktop.jpg), [Finance screenshot](artifacts/demo-finance-desktop.jpg), [comparison screenshot](artifacts/demo-finance-comparison.jpg).

## Portable submission rehearsal

The packager created a 463-entry archive from runtime checkpoint `538690c`, containing committed source and the prebuilt UI. Every manifest SHA-256 matched; no `.env`, Git internals, raw data or installed dependencies were included. Six packager regressions cover inclusion/checksums, incomplete builds, dirty tracked changes, symlinks, existing outputs and tracked environment files.

A clean extraction at `/private/tmp/aventier-submission-rehearsal` created its own Python 3.13 environment and successfully ran `pip install -e .` without `.env` or API keys. The prebuilt app started directly through Python/Uvicorn on 4187, without an npm install or build. Browser and HTTP checks confirmed:

- Built JS/CSS return 200; the Finance UI and scoped comparison render and Build my plan opens the correct grouped-role pathway.
- Health reports real evidence, the directory contains 412 profiles, bootstrap exposes v1.2/2024–25 price metadata and OpenAPI has 22 paths.
- The direct plan stores its actual 50/0/50 weights and `completed:false`; the prepared guide returns200. The historical evidence view includes all four windows, including2015→2020, and the crisis-check disclosure.
- Unknown and malformed careers return consistent404/422 envelopes with request IDs.
- The repository's HTTP-only `pull_the_plug.py --freeze` rehearsal exits0: API available, valid envelopes, no mock statuses and no live-ad claim after unplugging. Adzuna data is honestly missing; the harness restores its live flag.

The final ZIP is rebuilt from the delivery commit. The final historical-stat font increase is followed by a fresh production build and browser check; all other runtime source matches the independently installed checkpoint. Its own `SUBMISSION.json` identifies the exact revision and per-file hashes. Use [portable startup](../../docs/launch/submission.md) and the [three-minute demo](../../docs/launch/demo-script.md). Temporary rehearsal servers are stopped after verification; the4186 preview remains available.

## Scope and limits

The primary demo is the CS/Finance evidence → explicit priority comparison → chosen route and next action. The broader20-role interest matcher and412-profile directory are secondary. Affinities and mappings remain preliminary; historical checks do not validate personalised outcomes. Source redistribution rights and human catalogue verification still need review before a public release. Docker is unavailable here, so container execution remains unverified. There are no accounts, cross-device sync or live vacancies. The source README and launch handoff map the six core requirements and all17 checklist items without inventing judging scores or promising a win.

---

# Historical release records

The following records describe earlier checkpoints. Their branch names, data versions, test counts and publication status do not describe the current local CS/Finance delivery.

# Launch verification — 18 October 2026

This record supersedes the earlier 17 October prototype checks. Current release branch: `codex/hackathon-release`, created from the completed `codex/hackathon-launch` branch at the user's request. The complete product runs at http://127.0.0.1:4175 using `node scripts/run-app.mjs --production`, after the documented build. UI, experience API and canonical API share this one process and origin. This is a local running product and pushed integration branch, not a public deployment or a merge into main.

## Release gate

Run `PATH="$PWD/.venv/bin:$PATH" make check` from the repository root. The gate runs repository Ruff, core Python tests, app/integration/scanner tests, preserved prototype tests, frontend tests, formatting, TypeScript/Vite build and the tracked-file secret scanner. Gitleaks additionally runs when installed; its failures propagate.

Final `make check` exited 0:

| Check                                                     | Result                         |
| --------------------------------------------------------- | ------------------------------ |
| Core ML/contracts/decision/ETL/API                        | 438 passed, 2 optional skipped |
| App API, integration and scanner                          | 101 passed                     |
| Preserved prototype backend                               | 32 passed                      |
| Web state, notices, routes, export and chart gaps         | 17 passed                      |
| Ruff, Prettier, TypeScript/Vite, tracked-file secret scan | Passed                         |

**588 passing tests in total.** Two optional core checks require the external model or freeze environment; dependency lifecycle/TestClient deprecation warnings remain. The secret fallback checks tracked text files, not all Git history or untracked files.

The complete gate was repeated successfully after the release fixes at `f3cfc24`, using Node 20.20.2 and Python 3.13.16. The same test counts passed with Vite 6.4.4; a fresh `npm audit --json` reported zero vulnerabilities.

## Fresh setup and release rehearsal

`scripts/setup.sh` creates an absent Python environment, installs declared Python and locked web dependencies, builds the UI and checks the assembled application. `AVENIR_SETUP_PYTHON` selects the bootstrap interpreter; `AVENIR_PYTHON` remains the launcher's separate prepared-runtime override. `scripts/check-setup.sh` verifies the frontend build, real occupation evidence and both API layers without starting a server. The standalone `npm --prefix apps/web run api` now serves the assembled application, including canonical recommendations.

An independent fresh clone at `7718e95` installed successfully with new, unlinked `.venv` and `node_modules` directories. After updating that clone to `f3cfc24`, an engine-strict locked frontend install, production build and setup check also passed. No `.env` or provider keys were used. Actual production HTTP checks on a separate port verified:

- Built HTML, JavaScript, CSS and all seven local font assets return 200.
- Health reports real evidence; the catalogue contains 412 distinct profiles, bootstrap contains 21 curated profiles and OpenAPI exposes 22 paths.
- Amira receives three distinct canonical comparison tiers with return/risk scores, explanations and roadmaps. Unknown interest and career requests retain valid 422/404 error envelopes.
- The final Vite 6.4.4 bundle and canonical comparison also pass in the clean clone. Its temporary server was stopped; the user's app on 4175 remains running.

The actual `scripts/demo/pull_the_plug.py --base-url http://127.0.0.1:4175 --freeze` rehearsal exited 0: API up, valid envelopes, no mock status and no live-ad claim after unplugging. The live flag was restored. It warns that no Adzuna snapshot exists, so adverts remain explicitly missing.

The fresh installation exposed two inherited npm advisories. The targeted Vite 5.4.11 → 6.4.4 update also updates its esbuild dependency; React and the existing React plugin remain unchanged. Vite's [release policy](https://vite.dev/releases) lists the 6.4 security line, and its [file-serving advisory](https://github.com/vitejs/vite/security/advisories/GHSA-fx2h-pf6j-xcff) identifies the affected versions. The final root audit and independent clean install both report zero known vulnerabilities for this lockfile; that is not a general security certification.

## Actual browser checks

Chrome DevTools exercised the built React bundle against the assembled Python application, without keys or live AI:

- Fresh Amira journey: known architecture direction, five answers, three options, ranked choices, first-choice plan and canonical trade-off comparison.
- Route, personal note and completed action survive Home, resume and reload. Export contains those choices, the completed state and real source links/years. Saved RIBA opportunity remains accessible after Architect leaves the shortlist.
- All 412 occupations load through the enveloped catalogue endpoint. Search, sort, empty results, retry and lazy details work. SOC1133 keeps its older 2024 employment observation; SOC1112 labels wider-group pay and preserves its source note.
- Architect chart is visibly segmented at missing 2016, preserving the pay bridge and employment break at 2021. Text tables and keyboard year inspection remain available.
- Electrician defaults to earn-and-learn consistently with its supplied route content; an explicit saved route takes precedence.
- Guide replies show their source links. A delayed reply from the previous career is discarded. A failed request retries without duplicating the learner's question. Prepared guidance remains available without live providers.
- Malformed browser storage recovers to a usable application. Production errors retain the shared envelope; canonical confidence is low when reviewed catalogue inputs are unavailable, and genuine ML values remain unchanged.
- Desktop 1440px and mobile 390px My plan have no page overflow. Reduced motion, visible focus, labelled inputs and text chart alternatives are present.

Lighthouse on My plan scored **100 accessibility, 100 best practices and 100 SEO** at both widths, with no failed audits or run warnings. Automated audits cover this page and do not certify the entire application. [Compact audit record](artifacts/launch-lighthouse-summary.json), [desktop screenshot](artifacts/launch-plan-desktop.jpg), [mobile screenshot](artifacts/launch-plan-mobile.jpg).

After the Vite update, Chrome reloaded the final hashed bundle at both widths. Home → Resume plan preserved the Architect note, earn-and-learn choice and completed action. The mobile Electrician plan and canonical comparison rendered without page overflow. Neither page logged warnings or errors; built assets, bootstrap, matches and canonical recommendations returned 200. The preceding Lighthouse scores belong to the earlier unchanged UI audit, not a second Lighthouse run.

## Review and integration

Latest fetched main `6695e58` and Arsenii's real-artefact branch `a17aebb` are included, preserving authorship. The original dirty KATYATA checkout and teammate worktrees remain untouched. No manual edits were made to protected AGENTS.md or docs/contracts.md.

Independent reviews and `codex review --base origin/main` identified evidence caveats, missing-year interpolation, saved disclosure length, statistical labels, coverage labels and optional matcher readiness. Follow-up fixes were tested and reviewed. Core fixture generation is pinned to mocks as well as fixture loading; exact recommendation assertions were preserved, not weakened to accept real-data ordering.

The final upstream audit also integrated Arsenii's separate documentation correction `7ca933a` through merge `7e6c154`. `git cherry` confirms the remaining Nazar and Yehor branch patches already have equivalents in this release. The older ML import and `ilushka-context` branches share a tip; their implementation is superseded by the current loader/build pipeline and their other commits record migration/PR history. All nine real ML JSON artifacts are byte-identical to `a17aebb`. The corrected ML summary describes planned, uncommitted v1.2 work; this release does not claim those artifacts or the unpublished explanation checker. The shipped real evidence remains v1.1.

A second completion audit directly read both pages of the supplied GUTS brief and checked the requirement matrix against the implementation and recorded execution. The brief permits static datasets served through the app; live adverts and a live LLM are not required. All 59 local links in the root/app/verification/launch documents resolve. Changes after the final runtime gate are documentation-only, so that gate and browser evidence still cover the shipped application. Draft PR creation is the remaining repository workflow item.

## Limits and next release work

Matching covers 20 calibrated roles; the evidence directory covers 412. Interest affinities and mappings are preliminary, with synthetic matcher development labels. Backtests concern historical market signals, not personalised recommendation accuracy. Full-time employee medians are not starting pay, research exposure is not job-loss probability, and historical demand is not a forecast. Group estimates, provisional observations, missing values and source disagreement stay explicit.

Production excludes synthetic catalogue metrics and unreviewed canonical route rows. Editorial pathway and opportunity examples still require local eligibility/availability checks. Source redistribution rights and human catalogue verification need the team's review before public release. Docker/Compose definitions are supplied, but Docker was unavailable here, so container execution is unverified. The plan is browser-local; accounts, cross-device sharing, adviser dashboards, live vacancies and payment flows are future work. Business pricing, school targets and funding requests are untested pilot hypotheses.

## Publication status

The completed launch and release checkpoints are committed and pushed to `origin/codex/hackathon-release`; the earlier launch branch remains available. A draft PR description is prepared in [docs/launch/pull-request.md](../../docs/launch/pull-request.md). The GitHub connector returned404. Automatic approval review rejected use of stored Git credentials and an authenticated-browser fallback without specific authorization; no credentials were retrieved. The user's subsequent instruction was to make a new branch, which is complete; it was not treated as authorization to retry the rejected access methods. The PR has not been opened. [Compare the pushed release branch](https://github.com/yehorm14/Avenir/compare/main...codex/hackathon-release?expand=1).
