# Avenier live demo: 10 minutes (6:30 demo + 3:30 questions)

Format from the judge: 10 minutes per team for the demo and questions, two judge teams, strict timing. Live demo only. The one slide is `docs/launch/team-18-thank-you.html` (open it from the file system, full screen, F11).

App: http://127.0.0.1:4175 (production build of the latest main). Menu labels: Home, Quiz, Jobs, My plan, Chatbot. Inside My plan: My plan, Your matches, Your pathway, Opportunities, The evidence. Brand: Avenier.

Wording rules (AGENTS.md): say "worth exploring", never "you should". Say "history, not a forecast". Exposure is a research estimate, not job loss. If a number on screen differs from this page, read the screen.

Requirement key: 1 multiple sources, 2 API-first, 3 three layers, 4 engineering standards, 5 cohesive UX, 6 responsible AI.

Measured on main 2059d30: core 480 passed / 3 skipped, app API 142, integration and scripts 57 / 3 skipped, prototype 39 / 2 skipped, web 55; 773 tests, 0 failures; ruff and secret scan clean. The only failing check is freeze mode: the catalogue snapshot is not built because the curated CSV rows are unverified. Say this openly if asked.

## Pre-show checklist (6 lines)

1. Open http://127.0.0.1:4175/api/health: status "ok", careers 21, ml_mode "real", guide_mode "llm_grounded".
2. Wi-Fi on, and you know where its switch is. The Chatbot needs the network; everything else does not.
3. Browser zoom 125% or more; all five tabs visible: Home, Quiz, Jobs, My plan, Chatbot. Notifications off, power plugged in, screen sleep off.
4. Tabs ready: Home (#/discover), http://127.0.0.1:4175/docs, and the thank-you HTML (file://) in its own window. Do not call any text-to-speech route.
5. Rehearse the Chatbot question once (replies are cached on disk, free-tier quota is small). Do not rehearse more.
6. Agree who holds the keyboard for each block below and who answers which question.

## Demo plan (6:30)

### Block 1: 0:00 to 1:30. Frontend person (Illia or Max): Amira. Proves 5, 3

Clicks: **Home** (http://127.0.0.1:4175/) -> on the Amira card ("Amira, 17, S6 in Glasgow") click **Try architect** -> **My plan** opens on Architect alone (£47,143, -4.3% a year). Then click the **Your matches** tab (or go to #/matches): Architect next to the two alternatives, IT business analyst or systems designer (£60,288, +7.1%) and Actuary, economist or statistician (£53,342, +23.3%), with her weights Pay 15% / Interest 55% / Expected need 30%.

Say: "Amira is 17, in Glasgow, good at maths and art. Her first idea is architect, and she worries about AI. One click sends her answers to the API and her priorities become weights: interest 55, pay 15, demand 30 percent. Her idea stays first, the app puts alternatives next to it, and it shows that architect's trend is negative. And we never just hand her the popular or best-paid role: the picks come in three kinds, ambitious, balanced and lower risk, plus a hedge career, so a risk-averse student gets a low-volatility option on the same screen."

Expected figures (POST /api/discovery): Architect fit 54.62, median pay 47,143 GBP, trend -0.0432 a year relative to typical.
If it breaks: reload (F5); if still stuck, open a spare My plan tab (the plan is saved in this browser).

### Block 2: 1:30 to 4:00. Arsenii: data, sources, ML. Proves 1, 6

Clicks: **Home** -> **Explore finance** (Finance and investment analyst, £50,330) -> scroll to **Statistics for this role**. Scroll in this order: pay -> sources and years -> real pay against CPIH -> automation exposure -> **Hedge careers** -> **Crisis checks**. (The same panel is on **Explore CS** for Software developer; the Architect profile under Jobs shows pay, trend and exposure but not this panel.) Then Home, scroll to **Careers at BlackRock, in numbers**. Backtest (if time): **My plan** -> **The evidence** tab -> **How simple rules held up** -> choose the window **2019 -> 2024**.

Say, in order:
- "Every figure carries its source and year. Finance and investment analyst: 50,330 GBP median, full-time employees, 2025, provisional (ONS ASHE). Pay is deflated by CPIH, so the history is real pay in 2024/25 prices. Read the numbers on the screen, not from memory."
- "Automation exposure is from ILO WP140 with a DfE cross-check, Spearman 0.78 over 400 occupations. It is a research estimate, not job loss."
- "Hedges come from shared ESCO skills: the panel names the hedge careers and how many skills they share (read the screen). Crisis checks have a placebo test: COVID passes; cost of living and 2008 fail, so they are excluded from recommendations. We show the failure."
- "This is the point of the risk side: the same rules give general specifications for any occupation, not a story about a few popular jobs. Pay history, employment volatility and how an occupation held up in past shocks feed a risk score, so next to the exciting choice there is always a steadier, lower-volatility one, and the student sees why."
- "The backtest tests two naive rules, not our picks: in the 2019 to 2024 window the top third by pay had -6.4% median real pay growth, all occupations -0.9%. Employment is not comparable across the 2021 code change, so that window shows pay only. A bad result, and we show it."
- BlackRock card: "Official facts carry page numbers: about 24,900 employees at 31 December 2025, 2026 Proxy p.37. Salary ranges are self-reported on Glassdoor and labelled so. It is a static snapshot dated 18 October 2026."

If it breaks: go to **Jobs**, open any profile; same pay and sources. Drop the backtest first, then crisis checks; keep sources and exposure.

### Block 3: 4:00 to 5:15. Backend person (Nazar or Yehor): API, layers, tests, offline. Proves 2, 3, 4, 1

Clicks: open http://127.0.0.1:4175/docs (OpenAPI page; raw JSON at /openapi.json). Expand `POST /api/v1/recommendations`. Then show the repo tree: apps/web, packages/decision, packages/adapters, apps/web/api. Show `.env.example` (empty keys). Then switch Wi-Fi off, reload Home (F5), click **Try architect** again.

Say: "The API comes first: the decision API lives at /api/v1 and every answer uses one envelope with data, error and meta, a request id and source status. Three layers: apps/web is the UI, packages/decision is pure rules with no network and no model, packages/adapters and apps/web/api bring in data. Tests: 773, 0 failures; ruff and the secret scan are clean; keys live in .env, and only the empty .env.example is committed. Now I pull the plug." (Wi-Fi off, reload.) "The same plan loads from committed snapshots. Missing live adverts are labelled missing."

If it breaks: if reload shows an error, say the local API cannot be reached, turn Wi-Fi back on and continue from the saved plan tab. Do not call a blocked page proof of offline mode.

### Block 4: 5:15 to 6:15. Arsenii: Chatbot and what stays human. Proves 6, 2

Wi-Fi back on (check it first). Click **Chatbot**. Choose career **Actuary, economist or statistician**. Type exactly: `I want to work as a quant researcher at BlackRock` and press Enter.

Point at: the badge ("Written by the model from this role's evidence"), the tools_used chips if shown (the BlackRock lookup is get_employer), the "Sources for this answer" links, and the AI-written label.

Say: "Ranking is deterministic and never touches the model. The model only writes from tool results for this role. Every number in the reply is checked against the evidence pack, and banned phrases like 'you should' are blocked. With no key, or on a failed check, you get a prepared answer, labelled as such."

Do not promise the reply wording. Do not retry more than once.
If it breaks: if it says "Prepared guide" or "did not pass the number checks", say: "That fallback is by design; the guide always answers." Continue.

### Block 5: 6:15 to 6:30. Close

Switch to the thank-you page (team-18-thank-you.html, full screen). Say: "Avenier. Thank you."

## Q&A (3:30)

Brief requirements:

| # | Question | Show | Who answers |
|---|---|---|---|
| 1 | Multiple sources | Statistics for this role (sources, years); `snapshots/ml/sources.json` (12 registered sources); docs/data-sources.md | Arsenii |
| 2 | API-first | http://127.0.0.1:4175/docs; docs/contracts.md; apps/web/api/README.md | Backend |
| 3 | Three layers | apps/web/src, packages/decision, packages/adapters, apps/web/api; mermaid architecture diagram in README.md | Backend |
| 4 | Engineering standards | Makefile; packages/decision/tests; apps/web/api/tests; scripts/check_secrets.py | Backend |
| 5 | Cohesive UX | Home -> Try architect -> My plan -> Your matches; skip link, role=status and role=alert regions, keyboard focus (apps/web/src/App.tsx) | Frontend |
| 6 | Responsible AI | Chatbot badge and sources; apps/web/api/guide_llm.py (number check); AGENTS.md rule 1 | Arsenii |

Submission Checklist lines (docs/launch/README.md holds the numbered table; the exact wording of lines not marked (verify) was matched there):

| Checklist line | Where | Who |
|---|---|---|
| One named user and decision | Amira, 17, Glasgow; AGENTS.md section 1; Home Amira card | Frontend |
| Two independent sources | Statistics for this role: ONS ASHE pay and ILO WP140 exposure with DfE cross-check; /api/careers/2451/evidence-pack | Arsenii |
| Normalisation and comparison | CPIH-deflated real pay; packages/decision/tests/test_normalise.py; My plan three picks against first idea | Arsenii |
| End-to-end path | Home -> Try architect -> My plan -> route page (/api/path/2451?nation=Scotland) | Frontend |
| OpenAPI | http://127.0.0.1:4175/docs and /openapi.json (live; the committed docs/openapi.json is the older team API copy) | Backend |
| Layer separation | packages/decision/README.md (no I/O); packages/adapters; apps/web/src | Backend |
| Unit tests | packages/decision/tests; `npm --prefix apps/web test` (55) | Backend |
| Integration test | apps/web/api/tests (142 app API tests) | Backend |
| Graceful failure | Wi-Fi off and reload; Chatbot "Prepared guide" fallback; retry buttons on failed loads | Backend, Arsenii |
| No secrets, inputs validated | .env.example (empty keys); scripts/check_secrets.py clean; HTTP 422 on invalid input (apps/web/api/README.md) | Backend |
| README | README.md; docs/launch/README.md | Any |
| Setup | README.md run section; scripts/setup.sh; docs/launch/submission.md | Backend |
| Architecture diagram and trade-offs | README.md and docs/launch/README.md (mermaid diagram); docs/decisions.md | Backend |
| Accessible interface | Skip link, role=status and role=alert regions, keyboard focus and radiogroup quiz (apps/web/src/App.tsx). Screen-reader test not run (verify) | Frontend |
| Source and recommendation explanations | Statistics for this role; template decision explanation (ai_written false) | Arsenii |
| AI fallback | No key -> prepared answers; failed number check -> prepared answer; apps/web/api/guide_llm.py | Arsenii |

Hard questions, honest answers:
- Is an LLM ranking careers? No. packages/decision is deterministic and has no network.
- Why not just show the most popular or best-paid roles? Because that is what every careers site already does. The engine scores fit, return and risk for every occupation with complete data, picks an ambitious, a balanced and a lower-risk option, and adds a hedge career that shares skills but held up better. A risk-averse student gets a low-volatility choice with the evidence behind it.
- Is the data live? No: committed snapshots, each number with a source and year.
- Is every check green? 773 tests, 0 failures; the one failing check is freeze mode (catalogue snapshot not built because curated CSV rows are unverified).
- Matcher accuracy? 30 synthetic profiles only (hit@3 0.9 keyword_tags, 0.933 embed_tags, snapshots/ml/fit.json). No real learner labels scored; it covers 20 careers.
- Number check limits? It checks numbers and banned phrases, not whether a claim is true.
- Cache? Accepted guide replies are cached on disk for replay; do not say "nothing is stored".
- Licences? Not yet checked (licence_checked_by is empty); Adzuna adverts are missing.

## If it breaks (summary)

- App down: restart from the repo root with `node scripts/run-app.mjs --production`; meanwhile talk through the Q&A table.
- Chatbot slow or quota out: the prepared answer is the feature; say so.
- Wi-Fi demo fails: skip it and state that the data is committed snapshots.
- The served OpenAPI title reads "Avenier API" after the rename; check it once at /docs before the demo.
- Not verified: the Chatbot reply text, the exact look of the tools_used chips, and the thank-you page opened as file:// in the presenting browser (verify before going on).
