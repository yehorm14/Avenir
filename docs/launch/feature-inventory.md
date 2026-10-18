# What Avenier has

Main at 2059d30, checked against the running build (http://127.0.0.1:4175) and the source files named in brackets.

## Frontend

- Five-tab top bar: Home, Quiz, Jobs, My plan, Chatbot. [apps/web/src/App.tsx]
- Amira's journey: "Try architect" opens a plan that keeps her own idea beside alternatives, including a hedge. [App.tsx]
- Matches page: pay, interest and expected-need sliders re-rank the list live. Up to 3 careers can be shortlisted. [App.tsx]
- Jobs directory: 412 occupations, searchable, with a profile each. [GET /api/catalogue returns 412; Jobs.tsx]
- Evidence page: a backtest over four windows. In 2019-2024 the top third by pay (n=99) had median real pay growth of -0.0642; all occupations (n=291), -0.0088. [/api/bootstrap backtest]
- BlackRock employer card: roles, official facts with page numbers (about 24,900 employees, 2026 Proxy p.37) and the Smart Start route for school leavers aged 16 to 24. [public/employers/blackrock.json]
- My plan: checklist, saved opportunities and a downloadable plan, stored in the browser only, no account. [MyPlan.tsx, store.ts]

## Backend and the LLM guide

- One FastAPI process serves the UI, the /api/v1 decision API and the experience routes. No key is needed to run. [apps/web/api/application.py]
- The career ranking is deterministic rules. packages/decision makes no network or model calls. [packages/decision/README.md]
- The guide receives the role's evidence pack, the quiz profile, the last 6 turns and five read-only tools: get_role_stats, search_jobs, compare_roles, get_career_path, get_employer. [guide_llm.py, guide_tools.py]
- Number check: a reply is shown only if every number appears in the evidence pack or a tool result and it avoids banned phrases such as "you should" and "guarantee". Otherwise the prepared answer is served. [guide_llm.py]
- Fallback: on timeout, error, failed check or no model, the prepared reply is shown. A second key is used on HTTP 429 or 403. [guide_llm.py]

## ML and data

- 412 UK occupations in the ML snapshots, 14 metrics each, all "preliminary". Pay median exists for 409. [snapshots/ml/occupations.json]
- Automation exposure: ILO with a DfE cross-check, Spearman 0.78 (n=400). [snapshots/ml/eval.json]
- Hedge check: 83.6% of top-3 hedges are also related in O*NET, against 27.8% for random picks at the same level. The reference is partly circular. [eval.json]
- Crisis placebo test: COVID passes (ratio 2.021, threshold 1.25). Cost of living (1.215) fails and is hidden. [snapshots/ml/crises.json]
- Skills England Occupations in Demand 2025: 368 occupations, 62 Critical, 125 Elevated, 181 Not in high demand. [apps/web/src/occupationDemand.ts]

## Verification

Measured on main 2059d30 (Windows 11, Node 24, Python 3.13):

- Core 480 passed, 3 skipped. App API 142. Integration and scripts 57 passed, 3 skipped. Prototype 39 passed, 2 skipped. Web 55.
- 773 tests, 0 failures. Ruff and the secret scan are clean.
- The freeze-mode check fails only because the catalogue snapshot is not built, so the curated CSV rows are unverified.

## AI use

- Where: Gemini powers the chat guide, with tools over our data and the number check above. Coding agents wrote code that the team reviewed.
- What stayed human: the career ranking is deterministic rules, and the student makes the choice.
- How output is checked: every number must appear in tool results; otherwise the prepared answer is shown.
- Without AI: prepared answers are served and the app runs offline from committed snapshots.

## Limits and what we do not claim

- Survivorship bias: the universe is occupations that exist today.
- 2025 ONS figures are provisional.
- Everything is history, not a forecast. Scores are relative to the loaded careers, not probabilities.
- ILO exposure measures tasks that could be automated. It is not job-loss risk.
- The matcher was developed on 30 synthetic profiles over 20 careers; no real learner labels have been scored.
- The catalogue is not human-verified.
- Glassdoor and Levels.fyi figures are self-reported.
- Only the COVID crisis check passes; the tech slump is category-level and low confidence.
- BlackRock is one employer from a static snapshot, and two official links are marked "verify".
- We have not run the live guide or voice routes for this document, so quota and live reply quality are not claimed.
