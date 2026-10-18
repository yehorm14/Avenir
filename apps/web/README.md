# Avenier application

The complete React/Vite + FastAPI product lives here. See the [root setup and architecture](../../README.md) and [launch acceptance matrix](../../docs/launch/README.md).

From the repository root after installing dependencies:

```sh
npm --prefix apps/web run build
node scripts/run-app.mjs --production
```

Open http://127.0.0.1:4175. One service serves the UI, the experience API and the team's canonical `/api/v1` API using the shared envelope. `/docs`, `/openapi.json` and `/health` are on the same origin. No credentials are required. Use the launcher without `--production` for Vite development; both modes expose the same API format.

The primary menu is Home, Quiz, Jobs, My plan and Chatbot. Home retains the Computer Science and Finance dashboards. Chatbot opens a general career conversation at `#/guides`; career-specific links such as `#/guides/2134` still use that career's evidence context. The current visual design and secondary plan navigation are preserved.

The user journey is known-direction or exploring conversation → three weighted options → three ranked choices → My plan. The plan shows the selected career, key figures, a career chat and a collapsible monthly checklist. Routes, completed actions and saved links persist in this browser; previously saved personal notes remain in the downloadable plan. Plans export as source-linked HTML for sharing or printing. Jobs independently browses 412 supplied evidence profiles; 20 roles have calibrated interest affinities and curated detailed pathways. Broader profiles clearly state missing route/matching coverage.

My plan is a single overview with no inner tabs or repeated comparison tables: the chosen career, key figures, chat and monthly checklist. View pathway opens the detailed routes. Saved opportunities and plan download remain available. Comparison tools remain on the Home dashboards; Jobs profiles and the pathway's evidence view retain detailed sources.

Job profile sources and attribution are available in a collapsed Sources disclosure at the bottom of each profile.

The plan uses the same prepared guide as Chatbot, with source links on evidence replies, connection recovery and cancellation when leaving the page. Related pathway exercises are labelled as examples rather than presenting a borrowed career family's skill list as occupation-specific requirements.

The eight-question quiz supports answer review, previous-question navigation, keyboard arrows and direct completion into career results. Question changes restore focus to the heading. Jobs profiles have shareable URLs such as `#/jobs/2134`; Back/Forward and refresh retain the expected career, and returning to the list preserves its current search and sort. Connection failures show a readable message and a retry action.

The focused hackathon entry now opens `#/computer-science` or `#/finance` directly. Each dashboard switches between supported occupations, preserves the chosen role in the URL, and places observed pay/employment charts beside starting-pay guidance and practical next steps. “Build my plan” saves the selected career without claiming the user completed discovery; “Ask career guide” opens that career's guidance without changing the plan. Source details retain the API's publisher registry. The original quiz and full Jobs directory remain available. See the [three-minute demo](../../docs/launch/cs-finance-demo.md).

`api/main.py` contains the internal experience endpoints; `api/application.py` assembles the served production application and wraps them in the canonical envelope. Low-level API tests preserve the original payload checks; assembled application tests exercise the real served envelope, both API layers, validation, no-key decisions and static UI. `api/product_data.py` excludes unreviewed sample catalogue inputs from ranking and lowers confidence for that absence. It preserves genuine ML observations.

The UI follows the user-selected QuantSoc direction in [docs/design.md](../../docs/design.md): local Inter, charcoal and silver, blue evidence accents and a restrained desktop layout. No external fonts, copied assets, decorative quotations or cursive typefaces are used.

```sh
npm --prefix apps/web test
npm --prefix apps/web run format:check
npm --prefix apps/web run build
.venv/bin/python -m pytest apps/web/api/tests
```

Numbers retain provenance and missing-data caveats. Ranking is deterministic; guide replies are prepared and cited, with cancellation and retry. No hosted LLM, live vacancy feed, starting-pay prediction or validated psychological assessment is claimed. The root README documents responsible AI, data coverage, attribution and the boundaries of the demo.
