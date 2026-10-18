# Avenier: 10-minute run sheet (what to do)

Format: 10 minutes total. 6:30 demo, 3:30 questions. Live app only, one closing slide. Words are in `SPEECH.md`; this page is the driver's checklist.

## Links

| What | Link |
| --- | --- |
| The app | http://127.0.0.1:4175/ |
| Home | http://127.0.0.1:4175/#/discover |
| Your matches (Amira's picks) | http://127.0.0.1:4175/#/matches |
| Finance role page (statistics panel) | http://127.0.0.1:4175/#/finance |
| Computer Science role page | http://127.0.0.1:4175/#/computer-science |
| Jobs (412 occupations, UK demand) | http://127.0.0.1:4175/#/jobs |
| The evidence (backtest) | http://127.0.0.1:4175/#/evidence |
| Chatbot | http://127.0.0.1:4175/#/guides |
| OpenAPI page | http://127.0.0.1:4175/docs |
| OpenAPI JSON | http://127.0.0.1:4175/openapi.json |
| Health check | http://127.0.0.1:4175/api/health |
| Closing slide (open from disk, press F11) | `docs/launch/team-18-thank-you.html` |
| Repo | https://github.com/yehorm14/Avenir |

## Before the clock starts (5 minutes before)

1. Start the app if it is not running. From the repo folder, in Git Bash:
   `node scripts/run-app.mjs --production`
   If it says the environment is missing: `/c/Users/garba/miniconda3/python.exe -m venv .venv && .venv/Scripts/python.exe -m pip install -e ".[dev]" && npm --prefix apps/web ci && npm --prefix apps/web run build`, then run the line above again.
2. Open http://127.0.0.1:4175/api/health. It must say `"status":"ok"`, `"ml_mode":"real"`, `"guide_mode":"llm_grounded"`. If `guide_mode` is not `llm_grounded`, the `.env` file with the Gemini key is missing from the repo folder; the Chatbot will give prepared answers, which is fine, say so.
3. Open these tabs in order, left to right: Home, http://127.0.0.1:4175/docs, the thank-you slide (file, F11 later). Zoom the app to 125%.
4. Wi-Fi on. Know where the switch is. Only the Chatbot needs the network.
5. Rehearse the Chatbot question once, exactly: `I want to work as a quant researcher at BlackRock` on Actuary, economist or statistician. Once only; replies are cached and the free quota is small.
6. Plug in power. Notifications off. Decide who holds the keyboard per block (below).

## The demo (6:30)

| Clock | Block | Driver | Speaker | Do this |
| --- | --- | --- | --- | --- |
| 0:00 | 1 Amira | Frontend (Illia or Max) | Frontend | Home tab. Scroll to the Amira card. Click **Try architect**. My plan opens on Architect (£47,143, −4.3%/yr). Click the **Your matches** tab (or type #/matches). Point at the three cards and the weights Pay 15% / Interest 55% / Expected need 30%. |
| 1:30 | 2 Evidence | Arsenii | Arsenii | Home. Click **Explore finance**. Scroll to **Statistics for this role**: pay line → source and year → real pay vs CPIH → automation exposure → **Hedge careers** → **Crisis checks**. Then Home, scroll to **Careers at BlackRock, in numbers**. If time: **My plan → The evidence** tab, choose window **2019 → 2024**. |
| 4:00 | 3 Engineering | Backend (Nazar or Yehor) | Backend | Tab 2: http://127.0.0.1:4175/docs. Expand `POST /api/v1/recommendations`. Show the response envelope. Switch to the repo folder, show `apps/web`, `packages/decision`, `packages/adapters`, `apps/web/api`, and `.env.example`. Then **Wi-Fi off**, back to the app, press **F5**, click **Try architect** again. Everything loads. |
| 5:15 | 4 Chatbot | Arsenii | Arsenii | **Wi-Fi on** (check the icon). Click **Chatbot**. Choose **Actuary, economist or statistician**. Type `I want to work as a quant researcher at BlackRock`, Enter. While it thinks, speak. Point at the badge under the answer, the links, the AI-written label. |
| 6:15 | 5 Close | Arsenii | Arsenii | Switch to the slide tab, press F11. Say the closing line. Stop talking. |
| 6:30 | Q&A | All | Owner per question | Use the table below. Short answers. Show, don't describe, when the screen is one click away. |

## If something breaks

| Problem | Do |
| --- | --- |
| Your matches is empty after Try architect | Press F5, click Try architect again. The plan is saved in the browser. |
| Statistics panel missing on the Finance page | Use **Explore CS** (Software developer) instead; same panel. |
| Wi-Fi off and the page errors | Turn Wi-Fi back on, say the local server was blocked by the OS, continue from the saved plan. Do not call a blocked page proof of offline mode. |
| Chatbot shows "Prepared guide" or "did not pass the number checks" | Say: "That fallback is by design; the guide always answers." Continue. Never retry more than once. |
| App down | In the repo folder: `node scripts/run-app.mjs --production`. Talk through the Q&A table while it starts (about 10 seconds). |
| Slide will not open | Say "Avenier, Team 18, thank you" with the Home page on screen. |

## Q&A: who answers what

| Question | Show | Who |
| --- | --- | --- |
| Multiple data sources | Statistics for this role (sources and years); `snapshots/ml/sources.json`, 12 sources | Arsenii |
| API first / OpenAPI | http://127.0.0.1:4175/docs; `docs/contracts.md` | Backend |
| Three layers | `apps/web/src` (UI), `packages/decision` (rules, no network), `packages/adapters` + `apps/web/api` (data) | Backend |
| Tests, lint, secrets | 773 tests, 0 failures; `apps/web/VERIFICATION.md`; `scripts/check_secrets.py`; `.env.example` | Backend |
| Cohesive UX, accessibility | Home → Try architect → Your matches; skip link, status and alert regions, keyboard quiz | Frontend |
| Responsible AI | Chatbot badge and links; `apps/web/api/guide_llm.py` number check; ranking never uses the model | Arsenii |
| Is an LLM ranking careers? | No. `packages/decision` is deterministic and has no network. | Backend |
| Why not just the popular roles? | Three pick types (ambitious, balanced, lower risk) plus a hedge career; risk from pay history, volatility and past shocks | Arsenii |
| Is every check green? | 773 tests pass; freeze-mode check fails only because the catalogue snapshot is unbuilt (curated rows unverified). Say it openly. | Backend |
| Matcher accuracy | 30 synthetic profiles, hit@3 0.90 keyword / 0.93 embeddings; no real learner labels; 20 careers | Arsenii |
| Licences | ONS OGL, ILO WP140 CC BY 4.0 with the adaptation disclaimer, Glassdoor and Levels.fyi self-reported and attributed; `licence_checked_by` still empty | Yehor |
| Is the data live? | No: committed snapshots, each figure with source and year; the app runs offline | Arsenii |
