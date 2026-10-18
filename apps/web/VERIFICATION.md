# Launch verification — 18 October 2026

This record supersedes the earlier 17 October prototype checks. Release branch: `codex/hackathon-launch`. The complete product runs at http://127.0.0.1:4175 using `node scripts/run-app.mjs --production`, after the documented build. UI, experience API and canonical API share this one process and origin. This is a local running product and pushed integration branch, not a public deployment or a merge into main.

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

## Review and integration

Latest fetched main `6695e58` and Arsenii's real-artefact branch `a17aebb` are included, preserving authorship. The original dirty KATYATA checkout and teammate worktrees remain untouched. No manual edits were made to protected AGENTS.md or docs/contracts.md.

Independent reviews and `codex review --base origin/main` identified evidence caveats, missing-year interpolation, saved disclosure length, statistical labels, coverage labels and optional matcher readiness. Follow-up fixes were tested and reviewed. Core fixture generation is pinned to mocks as well as fixture loading; exact recommendation assertions were preserved, not weakened to accept real-data ordering.

## Limits and next release work

Matching covers 20 calibrated roles; the evidence directory covers 412. Interest affinities and mappings are preliminary, with synthetic matcher development labels. Backtests concern historical market signals, not personalised recommendation accuracy. Full-time employee medians are not starting pay, research exposure is not job-loss probability, and historical demand is not a forecast. Group estimates, provisional observations, missing values and source disagreement stay explicit.

Production excludes synthetic catalogue metrics and unreviewed canonical route rows. Editorial pathway and opportunity examples still require local eligibility/availability checks. Source redistribution rights and human catalogue verification need the team's review before public release. Docker/Compose definitions are supplied, but Docker was unavailable here, so container execution is unverified. The plan is browser-local; accounts, cross-device sharing, adviser dashboards, live vacancies and payment flows are future work. Business pricing, school targets and funding requests are untested pilot hypotheses.

## Publication status

All application checkpoints are committed and pushed to `origin/codex/hackathon-launch`. A draft PR description is prepared in [docs/launch/pull-request.md](../../docs/launch/pull-request.md). The GitHub connector returned404. Automatic approval review rejected use of stored Git credentials and an authenticated-browser fallback; no credentials were retrieved. The PR has not been opened. [Compare the pushed branch](https://github.com/yehorm14/Avenir/compare/main...codex/hackathon-launch?expand=1).
