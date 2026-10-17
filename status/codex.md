# Status: Codex

Updated: 17 October 2026

Doing now: Combined Avenir app is complete locally on codex/complete-career-experience. Production preview http://127.0.0.1:4175; one-command launcher starts UI and API. See apps/web/README.md and VERIFICATION.md.

Done and merged: Imported all fetched Avenir branch tips into this local integration branch, preserving original authorship, plus Arsenii's exact latest KATYATA cb9e169 ML paths (46 files verified against source blobs). Built Apple HIG-inspired neutral/green quiz → five weighted matches → three ranked choices → first-choice roadmap, skills, university examples, opportunity directory, career-specific prepared guides, nominal/real pay, employee-job comparisons, historical test, alternatives, alumni kit, progress and plan download. Original prototypes and the original dirty checkout preserved. Nothing pushed or merged into remote main. No code-review workflow run.

Interfaces changed: New app-local /api/bootstrap, /api/matches, /api/path/{soc}, /api/guide, /api/health in apps/web/api. Existing protected interfaces and agent policy were not manually edited; owner's v2.1 contract branch imported and generated examples refreshed. Pure matching returns source-driven fit status. No secrets or live provider dependency.

Verified: 305 root tests passed with 1 optional model smoke skipped; 13 app API tests passed. Build/format/API Ruff/syntax/whitespace checks passed. Chrome DevTools 27/27 final assertions; all six main pages fit 390px, desktop no overflow, no console errors/warnings. Screenshots in apps/web/artifacts.

Blocked on: Nothing for local demo. Live conversational LLM, live opportunity updates, validated psychology/held-out matching evaluation, current course eligibility and overtime datasets are not claimed; UI and README explain these limits. Publishing and formal review remain for the team.
