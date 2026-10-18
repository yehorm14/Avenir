# Launch verification — 18 October 2026

This record supersedes the earlier 17 October prototype checks. Current release branch: `codex/hackathon-release`, created from the completed `codex/hackathon-launch` branch at the user's request. The complete product runs at http://127.0.0.1:4175 using `node scripts/run-app.mjs --production`, after the documented build. UI, experience API and canonical API share this one process and origin. This is a local running product and pushed integration branch, not a public deployment or a merge into main.

## Release gate

Run `PATH="$PWD/.venv/bin:$PATH" make check` from the repository root. The gate runs repository Ruff, core Python tests, app/integration/scanner tests, preserved prototype tests, frontend tests, formatting, TypeScript/Vite build and the tracked-file secret scanner. Gitleaks additionally runs when installed; its failures propagate.

Final `make check` exited 0:

| Check | Result |
| --- | --- |
| Core ML/contracts/decision/ETL/API | 438 passed, 2 optional skipped |
| App API, integration and scanner | 101 passed |
| Preserved prototype backend | 32 passed |
| Web state, notices, routes, export and chart gaps | 17 passed |
| Ruff, Prettier, TypeScript/Vite, tracked-file secret scan | Passed |

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

## Limits and next release work

Matching covers 20 calibrated roles; the evidence directory covers 412. Interest affinities and mappings are preliminary, with synthetic matcher development labels. Backtests concern historical market signals, not personalised recommendation accuracy. Full-time employee medians are not starting pay, research exposure is not job-loss probability, and historical demand is not a forecast. Group estimates, provisional observations, missing values and source disagreement stay explicit.

Production excludes synthetic catalogue metrics and unreviewed canonical route rows. Editorial pathway and opportunity examples still require local eligibility/availability checks. Source redistribution rights and human catalogue verification need the team's review before public release. Docker/Compose definitions are supplied, but Docker was unavailable here, so container execution is unverified. The plan is browser-local; accounts, cross-device sharing, adviser dashboards, live vacancies and payment flows are future work. Business pricing, school targets and funding requests are untested pilot hypotheses.

## Publication status

The completed launch and release checkpoints are committed and pushed to `origin/codex/hackathon-release`; the earlier launch branch remains available. A draft PR description is prepared in [docs/launch/pull-request.md](../../docs/launch/pull-request.md). The GitHub connector returned404. Automatic approval review rejected use of stored Git credentials and an authenticated-browser fallback without specific authorization; no credentials were retrieved. The user's subsequent instruction was to make a new branch, which is complete; it was not treated as authorization to retry the rejected access methods. The PR has not been opened. [Compare the pushed release branch](https://github.com/yehorm14/Avenir/compare/main...codex/hackathon-release?expand=1).
