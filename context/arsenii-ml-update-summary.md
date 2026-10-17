# arsenii: ML update summary

- **Owner:** Arsenii (human) / Claude Code (agent)
- **Branch:** `arsenii/ml-update-summary`
- **PR:** draft, "arsenii: ML slice update summary"
- **Status:** ready for review

## Task
Yehor asked for an explicit written summary of everything done in the ML slice. Docs only: `docs/updates/2026-10-17-arsenii-ml.md`. No code, data or contract changes.

## Done so far
- Wrote the summary: data sources (loaded and dropped), pipeline, every work package with results, artefacts, loader, matcher service, explanation checker, tests, the two reviews, the v1.2 fix pass, limits, asks.

## Blocked on
- Nothing for this PR. The real ML artefacts (v1.1, matcher, v1.2) come in a separate PR.

## Open questions (for humans)
- 2008 crisis off the cards? Cost-of-living window? Pull-the-plug design? Track-record label? (Section 10 of the summary.)
- Matcher labels from 2 or 3 people; confirm the 20 demo careers.

## Marked (verify)
- ILO WP140 licence (CC BY 4.0 per the saved page; not re-checked on the live page).
- Test count for the uncommitted `test_explain.py`.
- Whether queued v1.2 items (coverage tracking, loader robustness, pay ceiling fallback, title lookup, 2015 window, in-house exposure rerun) get done before the freeze.
- Revised ASHE 2025 release date.

## Next step
Arsenii pushes the real artefacts (v1.1 plus matcher plus v1.2) to Avenir as one PR, then fixes the lint findings PR #2 reported.
