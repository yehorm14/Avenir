# Aventir — sprint 1

Illia requested a restart on 17 October 2026: small sprints, React frontend, FastAPI backend, name Aventir. First page: a career exploration landing screen using the Trading 212 investing-app layout, confirmed explicitly in chat.

## Reference and design

Reference supplied by Illia: https://community.trading212.com/t/your-home-screen-just-got-a-new-look/87886/3 . The original post's HomeTab image has been inspected in the browser.

- Dark upper research area, subtle cyan lighting, blue interactive chart, rounded dark widgets, white lower career browser/watchlist.
- Palette: black-blue #080e12, charcoal #192126, white #ffffff, cyan #00b9e8, positive #20b980, negative #f46672.
- Type: DM Sans; tabular chart values; compact, readable labels.
- Desktop: career list, main chart and research panel. Mobile: reference-inspired stacked widgets and career list.
- Career graphs represent actual available evidence, never simulated market prices.

## Deliverable

One page: browse/search the complete occupation catalogue returned by the official ESCO API, select a career, inspect its skills and available UK evidence, save it, and reflect on interests through the backend's OpenAI integration. Quiz, accounts and subsequent full pages are later sprints.

## Data and architecture

- SQLite database of all occupation profiles exposed by the imported ESCO API version, including essential/optional skill relationships, source URI and retrieval metadata.
- ONS public time-series API for UK industry vacancy history. Industry context is explicitly distinguished from occupation-level demand. Observations, units, release dates and periods remain inspectable.
- Existing verified National Careers Service salary references enrich matching occupations only; no automatic salary inference for unmapped careers.
- FastAPI serves the career search, detail, chart data, source metadata and AI reflection endpoints. The built React app is served by the same origin in production.
- OpenAI credentials stay in the ignored backend environment file. No API keys in frontend variables, generated assets, tests or logs. AI explains supplied evidence; it cannot invent chart values.
- Data gaps are visible. The complete API catalogue is not a claim that every possible job title has independent UK salary or hiring statistics.

## Work

- [x] Import the complete API catalogue: 2,942 distinct occupations; five skill-data gaps marked explicitly.
- [x] Import four real ONS series: 303 observations each; units, geography, chronology and missingness verified.
- [x] Implement FastAPI and server-side OpenAI access: 11 tests pass; real provider and UI reflection verified.
- [x] Build the first React page from the inspected reference.
- [x] Verify build, browser interactions and responsive design. Running at http://127.0.0.1:4174; desktop/mobile accessibility snapshots score 100. See VERIFICATION.md.

The prior Pathfinder implementation and protected shared contracts are preserved. The user authorised this restart; this sprint supersedes the old visual direction and Node API choice. No agent teams or review gate are launched, following AGENTS.md.
