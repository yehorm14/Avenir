# Avenir

The integrated career-discovery app. Eight psychology-informed questions lead to five career matches. Adjust Pay, Interest and Expected need, rank three choices, then explore a personal pathway, practical skills, university examples, opportunities, and a career guide. The overview keeps the other two choices visible and tracks small next steps. Progress stays in the browser; no account or API key is needed.

## Run

From the repository root, with Node 20+ and Python 3.12+:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/web ci
node scripts/run-app.mjs
```

Open http://127.0.0.1:4175. The API runs on 8015. Ctrl+C stops both processes. AVENIR_PYTHON can point to another installed Python environment. On Windows use .venv/Scripts/python.exe for installation.

For a production-build preview, start `npm --prefix apps/web run api` in one terminal. In another run `npm --prefix apps/web run build`, then `npm --prefix apps/web run preview`. Development and preview proxy /api to the local Python API. No external fonts or live provider credentials are needed.

## What was combined

- Max's complete prototype at e928ad8: local preferences, career flow, multi-stage pathway planner, university/apprenticeship routes, skills, alumni advice, inflation comparison and opportunity concepts. The original prototype is preserved.
- Arsenii's exact committed ML artefacts in snapshots/ml, including the latest cb9e169 from the original team repository: occupation evidence, histories, embedding-based interest affinities, skill-overlap alternatives, resilience and backtests. Every metric and history point passes through unchanged, with its supplied status.
- Nazar's API and decision branches, Yehor's catalogue, adapters, v2.1 contracts and frontend handoff, the integration harness, and Illia's earlier explorer. Original branch commits retain their authorship. The canonical new experience is apps/web; earlier apps remain as source references.
- The user's latest notes: broad questions; five adjustable matches; three ranked choices; a first-choice pathway; broad degrees where appropriate; hard and human skills; study/opportunity discovery; individual guide identities and browser text-to-speech; nominal/real pay and employee-job comparisons; local progress and downloadable plans.

See context/codex-complete-career-experience.md for provenance and verification.

## Evidence and limits

Ranking is deterministic Python. Pay and need compare available careers using percentile ranks of supplied median pay and 2021–2025 employment trends. Interest uses the supplied affinity table and its actual status. Positive weights are normalised around available values; zero weights use equal importance. Missing or suppressed metrics stay missing.

The quiz draws on work-interest psychology; it is not a validated psychological assessment. Model fit is preliminary and comparison indices are not probabilities. Need is historical evidence, not an LLM forecast. ASHE pay covers full-time employees and excludes the self-employed; median pay is not a starting salary. Pay bands show the middle 50%. Overtime and comparable working-hours figures are unavailable and are not fabricated.

Real pay is already adjusted using ONS CPIH to April 2025 prices. Bridged occupation estimates are dashed; employee-job lines break at the 2021 coding change. Charts have keyboard-readable year inspection and a text table. COVID and provisional-data caveats remain visible. The historical test shows Arsenii's original tiers and outcomes, including negative results; it does not validate the personalised quiz or priority sliders.

University and organiser links were checked against primary sources on 17 October 2026. They are examples, not university rankings, confirmed admissions eligibility, vacancies or an upcoming event feed. The directory filters by nation and online availability, supports saving/filtering/refresh, and opens organisers for current dates. Refresh rebuilds the curated directory view; it does not fetch live vacancies.

The conversational guides are explicitly prepared demos grounded in supplied facts and curated pathway examples. Arsenii provides embedding artefacts, not a hosted conversational LLM. Yehor's optional OpenAI-compatible adapter remains in packages/adapters/avenir_adapters/llm for later connection. Browser text-to-speech reads responses when available.

## Design

Apple system typography, cool neutral surfaces and one green action colour. Clear hierarchy, aligned content, progressive disclosure and simple charts follow Apple's official [layout](https://developer.apple.com/design/human-interface-guidelines/layout), [typography](https://developer.apple.com/design/human-interface-guidelines/typography) and [charting](https://developer.apple.com/design/human-interface-guidelines/charting-data) guidance. Responsive layouts, radio/slider keyboard controls, focus styles, reduced motion and modal focus containment are included.

## Verify

```sh
npm --prefix apps/web run format:check
npm --prefix apps/web run build
.venv/bin/python -m pytest
.venv/bin/python -m pytest apps/web/api/tests
```

Regenerate the frontend schema pack with `.venv/bin/python -m avenir_contracts.examples` after changing contract or ML versions. No protected contract was manually edited. No code-review workflow, PR, push or public deployment was run for this integration.

Source attribution: ONS (Open Government Licence); ILO Working Paper 140 (Gmyrek et al., 2025); ESCO (European Commission); curated institution and organiser links in src/content.ts. The saved registry retains original licensing notes; check them before public redistribution. AI coding assistance was used to integrate the app and write editorial guidance; those explanations are exploratory and official course sources remain the authority.
