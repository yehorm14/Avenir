## What this changes
A school leaver can move from a first career idea to three compared directions, choose a route, save actions and export a sourced plan. Combines the finished frontend, canonical backend and Arsenii's real artefacts; all 412 occupations are browsable while interest matching stays within the 20 supported roles.

This integration includes previously unmerged frontend/prototype history and committed evidence artefacts, so it is larger than the launch fixes alone. Original authorship is preserved. Latest fetched main `6695e58` and ML `a17aebb` are included. No direct main merge or force push is requested.

UI and both enveloped API layers now run from one key-free process. Added durable browser-local planning, cited/cancellable prepared guidance, canonical trade-off comparison, exact evidence labels, safe HTML export, production/container setup and CI release checks. Reviews closed missing-year interpolation, wider-group estimates, missing-input confidence, saved caveats, backtest interval labels, England planning coverage and optional matcher readiness.

Release branch: `codex/hackathon-release`. Reproducible setup/check scripts and the standalone API command have been verified from a fresh clone. Vite 6.4.4 closes the inherited npm findings without changing React or the product design.

## Context file
`context/codex-hackathon-launch.md`

## Checklist
- [x] `make check` passes: 438 core, 101 app/integration/scanner, 32 prototype and 17 web tests; 2 optional skips. Ruff, format, TypeScript/Vite and tracked-file secret scan pass.
- [x] Fresh clone installation, real production HTTP, strict locked frontend install and setup checks pass. npm audit reports zero vulnerabilities. Live freeze rehearsal passes with missing-advert disclosure.
- [x] Evidence retains actual source dates and caveats; missing/suppressed values stay missing.
- [x] England planning context and wider occupation-group estimates are labelled.
- [x] No credentials introduced; the redacted tracked-file scanner does not claim to audit all Git history.
- [x] Built UI exercised in Chrome at desktop/mobile widths. My plan Lighthouse accessibility/best-practices/SEO all 100. Screenshots and verification record included.
- [ ] I only touched my own slice's folders: this is the user's explicitly authorized cross-team integration, with deliberate upstream merges and isolated implementation/review slices.
- [ ] Needs a contract change: no manual edits to protected AGENTS.md or docs/contracts.md.

## Marked (verify)
Docker is not installed here, so Compose execution is unverified. Human catalogue/route verification and source redistribution rights remain open team work before public release. Personalised affinities are preliminary and development labels synthetic; no validated accuracy, starting salary, job-loss probability or forecast is claimed. Plans are browser-local. School pricing, recruitment and funding figures are untested proposals, not traction.

## Questions for reviewers
Confirm the integration boundary and remaining data/licence work before public release. Keep the canonical market comparison distinct from learner-adjustable interest priorities.

## How to test
1. Follow README: Python 3.12+/Node 20+, then `bash scripts/setup.sh` (or the documented manual commands).
2. Run `PATH="$PWD/.venv/bin:$PATH" make check`.
3. Start `node scripts/run-app.mjs --production`; open http://127.0.0.1:4175.
4. Follow `docs/launch/demo-script.md`: architecture idea, three directions, saved route/note/action, reload/resume/export, source inspection and prepared guide.
5. Browse a non-demo SOC, inspect parent-group/old observations and missing-year chart gaps. Inspect `/openapi.json` and both API success/error envelopes.

See `apps/web/VERIFICATION.md`, `docs/launch/README.md` and `docs/launch/business-case.md` for evidence, challenge acceptance mapping and the proposed pilot.
