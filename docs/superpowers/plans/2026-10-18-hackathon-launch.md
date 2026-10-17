# Aventier launch sprint

> Execution: autonomous integration, isolated implementation slices, independent reviews, verified commits and pushes. The user explicitly delegated product decisions and execution; do not stop at planning gates.

## Product brief

Amira is 17, studying in Glasgow, enjoys maths and art, and is considering architecture. Her decision is which career to explore first and what practical step to take this month. Aventier combines occupation earnings and employment, automation research, skills and route evidence to compare a first idea with alternatives, then saves a route and next actions. The student's priorities remain their choice.

The supplied GUTS challenge brief requires multiple sources, API-first design, separated experience/decision/provider layers, core unit tests and an integration test, reproducible setup, resilience, accessibility and responsible AI. Success is a complete, comprehensible decision journey, not a collection of statistics. A strong funding story comes from a useful product and an explicit pilot/business hypothesis; never invent traction, accuracy, customers or revenue.

## Design and constraints

- Keep the inspected QuantSoc direction: Inter, charcoal #0a0a0a, silver #dae0e7, muted #acb6c3, blue #6da2f8, restrained gold signal paths and floating navigation. No cursive fonts, testimonials, decorative quotations or copied assets.
- Home provides two clear starts and a returning user's plan. Jobs explores evidence; My plan turns exploration into an actionable persistent decision. Sources stay next to the claims they qualify.
- Preserve teammates' authorship and all existing dirty work outside this clean integration checkout. Work on codex/hackathon-launch and isolated checkouts for parallel edits. Do not alter protected AGENTS.md or docs/contracts.md.
- Import Arsenii's exact latest committed ML slice. Browse all supplied occupations, but keep matching restricted to occupations with calibrated affinities. Missing evidence stays missing. Histories retain their true years, coverage and code breaks. No invented courses, vacancies or forecasts.
- Canonical /api/v1 routes retain the team's consistent envelope and OpenAPI. The app's compatibility API must be explicitly documented; errors remain useful and validated.
- No live LLM is required. Prepared guidance is labelled; deterministic ranking works without AI or keys. Show returned source links and prevent stale replies crossing career conversations.
- Persistent progress is browser-local, with an honest data/control explanation. No new accounts, payment collection or analytics are needed for the demo.

## Task 1: Integrate latest team changes and establish a green checkpoint

Merge origin/main into the complete frontend branch, taking the reviewed canonical backend. Import origin/arsenii/ml-real-artefacts, preserving real and mock artefacts separately. Resolve generated examples by regenerating with the current contract. Run the full Python suite, app API suite, frontend format and build. Review changes, commit and push the integration checkpoint.

Interfaces: canonical API /api/v1 and app compatibility /api; ML data at snapshots/ml, mocks at snapshots/ml/mock.

## Task 2: Broaden evidence browsing safely

Expose a lightweight all-occupation catalogue from the app API and fetch complete profiles on demand. Keep bootstrap and personalised matching small. Jobs shows all supplied careers, search/sort, current salary and employment with exact observation years, honest unknown demand classifications, and detailed sourced charts. Uncovered routes have a clear fallback. Use public ML accessors. Correct misleading full-time and parent-group labels and verify notes/caveats in the UI and guide.

Tests first for API/catalogue coverage, source preservation, missing data, unsupported routes and matching boundary. Build and exercise real Jobs browsing, a non-demo occupation and empty results.

## Task 3: Make the decision and plan durable

Add an always-reachable My plan destination and Home resume action. Preserve the shortlist when redoing discovery. Persist route choice per career; make selected route, completed steps and saved opportunities survive navigation and refresh. Resolve saved opportunities independently of the current shortlist. Export a readable decision brief with ranked careers, priorities, route, progress, saved links and provenance. Make the export readable for a parent or adviser. Guard malformed local storage.

Verification: choose three careers, choose earn-and-learn, complete an action, save an opportunity, navigate Home, reload, resume, change shortlist, view saved item and inspect export.

## Task 4: Review trust and accessibility at every decision

Render guide citations from the API and cancel in-flight requests on career change. Add compact provenance and index explanations to match cards. Fix global keyboard focus contrast, mobile navigation and any overflow; respect reduced motion. Preserve clear loading/retry/empty states. Check desktop/mobile, keyboard, malformed storage, offline retry and guide race behaviour in Chrome DevTools. Run accessibility audits and review screenshots.

## Task 5: Package a reproducible product and pitch

Serve the production frontend, app API and canonical API from one documented process/container, with health checks and no keys. Add/verify clean setup, build/check commands, integration smoke checks, architecture and AI disclosure. Write a concise hackathon demo script, requirement-to-evidence matrix and business/pilot plan with assumptions labelled. Remove stale documentation and placeholder claims. Review the final diff, run actual stack tests/build and browser journey, commit and push working increments, open a small draft PR into main.

## Review focus

- Full catalogue must not dilute calibrated matching or load multi-megabyte histories at startup.
- Full-time versus all-employee coverage, historical versus forecast demand, old observation years and parent-group estimates must stay explicit.
- Returning to Home/repeating discovery must not silently destroy a student's choices.
- A pending guide response must never be attributed to another career.
- Saved opportunity links and exported action state must remain consistent after shortlist changes.
- Invalid browser state must recover without a blank application.
- Canonical error envelopes and API docs must survive integration; no secrets or private host data in commits.

## Checkpoints and evidence

Record work and decisions in context/codex-hackathon-launch.md, update TASKS.md and status/codex.md. Push after each coherent verified increment. Never force-push or merge main directly. Final evidence includes exact commits, tests, screenshots, start URL, known limits and draft PR.
