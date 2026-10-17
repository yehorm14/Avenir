# Status: Codex

Updated: 18 October 2026

Doing now: UK-demand Jobs section complete locally on codex/quant-soc-branch. Preview: http://127.0.0.1:4175/#/jobs.

Done and merged: Searchable, sortable text directory with electrician and plumber first. Removed decorative icons, generic tagline, repeated pay labels and Details buttons. Career names open pay quartiles, employee totals, official demand categories, real/nominal/jobs history, an editable two-year salary estimate and sourced sector outlooks. Published forecast horizons are preserved. Added canonical plumber SOC 5315. Nothing pushed or merged remotely; no formal review.

Interfaces changed: App-local bootstrap and career lookup expose 21 careers. Matching/discovery retain the calibrated 20. Missing plumber pathways return 404; guides disclose missing route coverage. Shared contracts and snapshots unchanged.

Verified: TypeScript/Vite build, Prettier and whitespace checks pass. All 33 app API tests pass, with one existing dependency deprecation warning. Browser checked priority order, search/sorting, plumber/software/finance profiles, historical chart modes and code break, keyboard inspection, salary calculations, empty-input validation and no desktop overflow or console errors. User preview refreshed. Screenshots: apps/web/artifacts/uk-priority-jobs-desktop.jpg and software-pay-outlook-desktop.jpg.

Blocked on: Nothing for this request. Exact two-year earnings and occupation-specific 2031 vacancy counts are not supplied by these sources; the UI labels estimates and qualitative outlooks explicitly. No plumber fit/pathway is invented.
