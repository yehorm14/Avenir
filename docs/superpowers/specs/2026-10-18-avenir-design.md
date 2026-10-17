# Avenir design spec

*18 Oct 2026. Source of truth for every slice. ML and training owned by Arsenii. Items marked "verify" were written from memory; `docs/data-sources.md` records what has since been checked.*

## 1. The product in one page

**One line:** Avenir is a portfolio manager for your future: it finds careers that fit you, shows their return and risk with real UK data, says how sure it is, gives you a hedge, maps the path in, and publishes how its own ratings held up in the past.

**Named user:** Amira, 17, S6 at a Glasgow school. Good at maths and art, thinking "computer science or architecture?", worried AI will hit the jobs she likes. No careers adviser has shown her anything outside what her parents and TikTok know.

**The one decision:** which career should I aim for, and what is my next step into it (which subjects, which route: degree, graduate apprenticeship, college)?

**Why combined data helps:** no single source tells her "this pays X now and Y mid-career, demand is rising here, its automation exposure is high but uncertain, a related role with the same skills is safer, and here are the three routes in from where you are". The join is the product. Every number carries its source, year, region and a confidence badge; missing numbers say "missing".

**Investment framing (the hook for this room):**

| Investing | Avenir |
| --- | --- |
| Suitability | Fit: the matcher's score between her profile and the occupation, plus "head start" (what she already has) |
| Expected return | Pay now, early-career pay, pay ceiling, real growth over ten years (ONS ASHE) |
| Market risk | Demand trend (employment series), shortage flags, live ad counts, regional lens, pay spread |
| Disruption risk | Automation exposure from published task-level research, with a second in-house estimate |
| Forecast uncertainty | A confidence level on every indicator, from granularity, sample size and recency |
| Diversification | A hedge career: the related role sharing the most skills with lower risk |
| Track record | The backtest: how our ratings from past years turned out 3 to 5 years later |

**Three picks, each compared against her first idea:** Ambitious (highest return among good fits), Safe (lowest risk among good fits), Balanced (best return per unit of risk). No single magic score; the components are shown.

**Ends in action:** a three-step roadmap with real routes (degree subjects, Scottish graduate apprenticeships, college), entry requirements against what she has, and one thing to do this month.

## 2. Demo flow (Sunday)

1. **About you.** Checklist of interests plus optional free text ("I like drawing and fixing things"). The matcher turns text into tags; Amira confirms them. Qualifications so far, location (Glasgow), one slider: how much automation risk worries you.
2. **Your first idea.** She types "architect".
3. **Three picks against your first idea.** Cards for Ambitious, Safe, Balanced, each with the seven rows above, sourced, badged for confidence, and the comparison to architect on each row.
4. **The hedge.** For the top pick: the related role sharing the most skills with lower disruption and market risk, with the shared skills listed.
5. **Automation slider.** She drags it; the picks reshuffle; the explanation changes. The LLM's prose cites only numbers on screen.
6. **Track record.** The judge presses "pick a past year": the ratings as of 2015 for these occupations, and what pay and employment did by 2020. Honest caveats on screen.
7. **Roadmap.** Three steps: Highers to take, route (degree vs graduate apprenticeship), first milestone, with live apprenticeship or course links labelled by nation.
8. **Pull the plug.** Switch off the live ad feed; the card keeps working on the snapshot with a badge.

## 3. Data sources

UK-wide sources carry the core, because Amira is in Glasgow and the England-only sources (Skills England, Find an Apprenticeship, National Careers Service) don't cover her. England-only data is used with a visible "England" label.

| # | Source | Gives | Scope | Status / verify |
| --- | --- | --- | --- | --- |
| 1 | ONS ASHE (annual, by SOC 4-digit, percentiles, age bands, regions) | Pay now, early-career pay, ceiling, spread; the backtest series back to 1997 | UK | Published tables; SOC 2000/2010/2020 changes in 2001, 2011, 2021 (bridge tables exist; verify) |
| 2 | ONS employment by occupation (APS/LFS via Nomis API) | Demand trend 2004+; regional employment | UK | Nomis has a public API (verify dataset ids) |
| 3 | DfE Occupations in Demand 2025 | Shortage flag and demand indicator | England | Downloadable; label as England |
| 4 | Skills England sector assessments 2026 | Industry context cards | England | Reports; label |
| 5 | ILO GenAI exposure index (2025, ISCO-08, 423 occupations) | Disruption risk, occupation level | International | Public scores; ISCO-08 to SOC 2020 crosswalk from ONS (verify) |
| 6 | Eloundou et al. 2023 task-level exposure (O*NET, US SOC) | Second exposure estimate; task-level evidence | US, via crosswalk | Public; crosswalk O*NET-SOC to UK SOC (verify) |
| 7 | ESCO (occupations, skills, tasks; downloads and API) | Hedge career (skill overlap), matcher training text, task list for in-house exposure | EU, multilingual | Open; maps to ISCO-08 |
| 8 | HESA Graduate Outcomes / Discover Uni data | Where each degree subject's graduates go; outcomes per course | UK | Downloadable CSV; broad subject groups |
| 9 | Discover Uni / UCAS course data | Degree routes and entry requirements | UK | Downloadable; entry requirements may need curation |
| 10 | Apprenticeships: apprenticeships.scot and Graduate Apprenticeships (Scotland); Find an Apprenticeship API (England); Wales and NI curated | Routes in, live adverts | Four nations | Scotland curated by hand for the 20 careers (no API assumed); England API needs a key |
| 11 | Adzuna API | Live ad counts and advertised pay by occupation keyword and region | UK | Free key; the one live source in the demo; cached, snapshot fallback |
| 12 | ONS wellbeing by occupation (APS, 9 groups); HSE stress by job group | Wellbeing and stress | UK | Coarse; shown with a group-level badge, never as occupation-level |

Scope: 20 occupations for the demo (40 in the ETL if time allows), chosen to span Amira's interests (maths and art) and all three tiers, keyed on SOC 2020 with ISCO-08 and ESCO ids. Candidate list for the team to confirm: software developer, data analyst, UX designer, architect, architectural technologist, civil engineer, structural engineer, electrical power networks engineer, building controls (BEMS) engineer, quantity surveyor, geospatial surveyor, actuary, accountant, graphic designer, animator/VFX artist, product designer, maths teacher, radiographer, electrician, marketing analyst.

Every number in `careers.json` carries `{value, source, year, region, granularity, n, retrieved_at}`.

## 4. Decision layer (pure functions, unit tested, no LLM)

Normalise every metric to a 0 to 100 rank across the occupation set. Components, each with a confidence level:

- **Fit** = matcher similarity (M1) × head-start factor (her qualifications vs entry requirements). Fit gates the picks: only occupations with fit above a threshold are eligible.
- **Return** = weighted pay now (ASHE median), early-career pay (age band), ceiling (p75), ten-year real growth.
- **Market risk** = inverse of demand trend (M4), shortage flag, live ad momentum, regional availability; plus pay spread (p10 to p90) as uncertainty of return.
- **Disruption risk** = ILO exposure (primary) blended with the in-house task-level estimate (M2); confidence widens when they disagree.
- **Risk** = weighted market risk and disruption risk; the automation slider moves the weight.
- **Picks:** Ambitious = max return among eligible; Safe = min risk among eligible; Balanced = max (return − baseline) / risk among eligible. Ties broken by fit.
- **Hedge** = for the top pick, the eligible occupation with the highest skill overlap (M3) and lower risk.
- **Comparison** = every component for the pick and for her first idea, side by side.
- **Confidence** = per indicator from granularity (occupation / group / estimate), sample size, data year, and source agreement; shown as a badge and used to widen displayed ranges.
- **Roadmap** = rules over routes data: subjects required, route options by nation, entry requirements vs head start, first milestone.

Explicitly cut from the demo: the what-if simulator (the slider is the only what-if), employer-site scraping, any single magic score.

## 5. ML and training work packages (Arsenii)

Run on the laptop GPU (`torch-cuda` env) or the cluster; artefacts ship as tables and small models; nothing licensed is involved, so all artefacts can live in the repo. Priority order by demo value.

**M5 first: the backtest (the track record).** CPU, tonight.
- For each year Y in 2010 to 2019: build the Avenir signal for all SOC 4-digit occupations using only data available at Y: pay (ASHE Y), ten-year growth to Y, demand trend (employment Y−4 to Y), pay spread. Assign tiers. Then measure pay growth and employment growth Y to Y+5.
- Report per tier: median pay growth, share with employment decline, worst case. Produce `backtest.json` for the "pick a past year" button.
- Bridge SOC 2010 to SOC 2020 with the ONS crosswalk (verify); where a code splits or merges, mark the occupation's confidence low.
- Exposure can't be backtested before 2022 without look-ahead. Separate, labelled "early evidence": since 2022, did high-exposure occupations (today's ILO score) show weaker ad growth (Adzuna) or employment growth (APS) than low-exposure ones? Three years, indicative only.
- Caveats on screen: few occupation-years, confounding, code changes.

**M1: interest matcher.** Laptop GPU, 1 to 2 hours.
- Zero-shot baseline: `BAAI/bge-base-en-v1.5` (verify licence) embeddings of ESCO occupation and skill descriptions; profile text → top occupations by cosine.
- Fine-tune with contrastive pairs: ESCO skill/task descriptions paired with everyday interest statements. Generate candidate statements with an ELM-hosted model, then human-review a subset (team of five, 30 minutes, about 300 pairs); hard negatives from superficially similar occupations.
- Evaluate on a held-out, human-reviewed set: top-5 hit rate vs keyword search and vs the base model. Report in the README. Similarity is a discovery aid, never a success prediction.
- Artefact: model folder (or just the embedding table for the 20 occupations if the fine-tune doesn't beat the baseline), `matcher_eval.json`.

**M2: in-house task-level automation exposure.** ELM-hosted model or cluster, 1 to 2 hours.
- For each of the 20 occupations' ESCO tasks, label exposure on a published rubric (the Eloundou et al. rubric: no exposure / direct / with tooling), with an LLM; aggregate to occupation; calibrate against the ILO score; report agreement.
- Output: exposure estimate with an interval and a disagreement flag. Shown as "research estimate", never "this job will disappear".

**M3: hedge career similarity.** CPU, 1 hour.
- ESCO essential and optional skills per occupation → weighted Jaccard or embedding similarity across all occupations in the set (extend to all ESCO occupations mapped to SOC if time).
- Sanity check against O*NET related occupations where a crosswalk exists; report overlap.
- Artefact: `hedge.json` with the top three related roles and the shared skills.

**M4: demand trend and nowcast.** CPU, 1 hour.
- Employment series per SOC (APS via Nomis): Theil-Sen slope over five years with a bootstrap interval; shortage flag from Occupations in Demand (England label); Adzuna ad counts for the nowcast and regional lens.
- Artefact: `demand.json` with trend, interval, flags.

**M6: AI evaluation set.** 30 minutes across the team.
- 50 free-text profiles with human-confirmed tags (for the matcher and the LLM tag mapping); 20 explanations checked for "cites only numbers in the response".

Cluster use: only if the fine-tune needs it; everything above fits the laptop. No model training is in the demo's critical path: the app runs on the zero-shot baseline and the published indices if M1 or M2 slip.

## 6. Architecture and repo

```
[ Experience ]   React + Vite: about-you, first-idea, three cards vs first idea, hedge, slider,
                 track record (pick a past year), roadmap, sources. Text twin for every chart.
      |  REST + OpenAPI contract
[ Decision ]     Pure Python: fit, return, risk, confidence, picks, hedge, comparison, roadmap rules.
                 Unit tested, no I/O, no LLM.
      |
[ Integration ]  Adapters, one folder each, snapshot fixture each:
                 ashe, employment (Nomis), occupations_in_demand, ilo_exposure, esco, hesa,
                 routes (curated four nations), adzuna (live, cached, timeout, snapshot fallback),
                 llm (ELM commercial for prose and tag mapping; template fallback)
[ Offline ]      ETL → careers.json with provenance; ML artefacts: backtest.json, matcher, exposure.json,
                 hedge.json, demand.json
```

Repo layout: `apps/web`, `services/api`, `packages/decision`, `packages/adapters/<source>/`, `packages/ml/` (Arsenii's scripts and eval reports), `data/` (raw downloads, gitignored), `snapshots/` (small committed fixtures and the artefacts above). `docker compose up` runs the API and web; no database needed for the demo (JSON artefacts loaded at start).

Stack as both team documents proposed: FastAPI (OpenAPI generated, pandas) and React + Vite.

## 7. Contract proposal for `docs/contracts.md` (Yehor's to adopt)

One envelope: `{ok, data, error{code, message, details}, meta{as_of, sources[{name, status, as_of, region}]}}`.

Endpoints:
- `POST /api/v1/profile`: interests, free text, qualifications, location, slider → confirmed tags, head start
- `POST /api/v1/recommendations`: profile, first idea → three picks, hedge, comparison, explanation, sources
- `GET /api/v1/careers/{soc}`: full card with provenance
- `GET /api/v1/careers/{soc}/hedge`
- `GET /api/v1/backtest?year=2015`: ratings then, outcomes 5 years later, caveats
- `GET /api/v1/routes/{soc}?nation=scotland`
- `GET /api/v1/sources`, `GET /health`

Data models: `Career` (soc2020, isco08, esco_id, title, metrics{pay_now, pay_early, pay_ceiling, pay_growth_10y, pay_spread, demand_trend, shortage, ads_now, exposure_ilo, exposure_inhouse, wellbeing, stress}, each metric as `{value, low, high, source, year, region, granularity, n, confidence}`), `Profile`, `Pick` (tier, career, components, vs_first_idea), `Hedge`, `BacktestYear`, `Route`, `Roadmap`.

Validation: all inputs schema-validated; unknown SOC → 404 with the envelope; slider bounded.

## 8. Responsible AI and the Children's Code

| Where AI is used | Check | Fallback |
| --- | --- | --- |
| Free text → interest tags (matcher, then LLM for phrasing) | User confirms tags before scoring; eval set M6 | Checklist only |
| In-house task-level exposure (offline, M2) | Calibrated against the ILO index; disagreement shown | ILO index only |
| Plain-English explanation (ELM) | May cite only numbers present in the API response; validated | Template from the same numbers |

What stays human: Amira sets priorities and chooses; the app suggests careers worth exploring and never says "don't". Exposure is a research estimate with confidence. The demo stores no personal data and needs no account; a real version would follow the ICO Children's Code (no profiling persistence for under-18s without a basis, data minimisation, plain-language notices).

## 9. Slices and timeline (now to Sunday midday)

| Slice | Owner | Tonight | Sunday morning |
| --- | --- | --- | --- |
| ML and training | Arsenii | M5 backtest, M4 demand, M3 hedge | M1 matcher eval, M2 exposure, M6 eval set |
| Data ETL | one | `careers.json` for 20 occupations with provenance; curated Scottish routes | 40 occupations if time; wellbeing and stress badges |
| Backend | one | Contract, adapters with snapshots, Adzuna with fallback | backtest and hedge endpoints, pull-the-plug |
| Decision logic | one | Scoring, picks, comparison, tests first | Confidence, roadmap rules |
| Frontend + glue | one | Quiz, cards vs first idea, hedge | Slider, track record view, roadmap, accessibility, README, diagram, pitch |

Timeline: 20:00 to 20:30 freeze the contract; 20:30 to 01:00 build on mock `careers.json`; overnight ML artefacts; 08:00 to 10:00 integrate real data; 10:00 to 11:30 tests, README, rehearsal; 11:30 freeze.

Cut order if time runs out: in-house exposure (M2), fine-tuned matcher (keep zero-shot), the regional lens, the wellbeing rows, 40 → 20 occupations. Never cut: the three cards vs first idea, the hedge, the backtest button, the roadmap, provenance badges, pull-the-plug.

Stretch (the "next" slide): watchlist with change alerts, careers-adviser view (Gatsby Benchmarks), practitioner clips as discovery, four-nation live apprenticeship feeds, Lightcast-grade demand data.

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| Backtest shows no separation between tiers | Report it honestly as the track record; the pitch becomes "we checked, and here is what careers data can and can't tell you" |
| SOC code changes break the series | ONS crosswalks; low-confidence flag on split or merged codes |
| England-only sources for a Glasgow user | UK-wide core (ASHE, APS, HESA, ILO, ESCO, Adzuna); England labels; curated Scottish routes |
| Coarse wellbeing and stress data | Group-level badge; never shown as occupation-level |
| Exposure framing | "Automation exposure, research estimate, confidence shown"; never "disappears" |
| Matcher fine-tune doesn't beat baseline | Ship the baseline; report the eval either way |
| Copyable by another team | The hedge, the backtest, provenance badges and pull-the-plug are the visible edge; rehearse the "why not ChatGPT" answer |
| Minors' data | No account, nothing stored, Children's Code note in the README |

## 11. Verification

- The spec renders on GitHub; the PR is mergeable; the context file has no placeholders.
- For the build itself: unit tests on the decision package; one integration test through `POST /api/v1/recommendations` with every adapter in snapshot mode; a provenance test that every metric has source, year and confidence; a backtest test that no feature for year Y reads data after Y; the demo runs from `docker compose up` with no keys present.
