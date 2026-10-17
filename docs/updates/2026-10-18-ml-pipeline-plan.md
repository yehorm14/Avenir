# ML pipeline plan after the backend merge

- **For:** Arsenii (owner of `packages/ml/` and `snapshots/ml/`).
- **From:** Yehor's side of the backend, written with Claude Code, Saturday 17 Oct, late evening.
- **Answers:** your summary `docs/updates/2026-10-17-arsenii-ml.md`, mainly sections 1, 3.3, 7.3, 8.4 and 10.
- **State:** `origin/main` at `3557df1`. Tests green after each merge (344 passed, 1 skipped, ruff clean).
- **Freeze:** Sunday 18 Oct, 11:30.

---

## 1. TL;DR

- Contract v2.1 is on main. It adopts your v1.1 fields and allows `snapshots/ml/` files up to 5 MB each.
- Your summary is merged (PR #10). We closed the stale PR #2. We added your 8 missing sources to `data/manifest.yaml`.
- We do not need your `validate_explanation`. The LLM adapter has its own checks.
- We need ONE PR from you on Sunday between 08:00 and 09:30: `packages/ml` plus `snapshots/ml`, same shapes as contract v2.1.
- Before 08:00 we need five answers: PR timing, `fit.json`, the final 20 demo careers, look-ahead (#13) and imputation (#17).

---

## 2. What is on main that touches your slice

### 2.1 Contract v2.1 (PR #4)

Files: `docs/contracts.md`, `packages/contracts/avenir_contracts/` (`vocab.py`, `models.py`).

| Your v1.1 change | What main does |
| --- | --- |
| `young_worker_share` | Added to `vocab.ML_METRICS` (now 14 ML keys). Absent or null means missing. |
| `evidence` on hedges (`title` or `estimate`) | Optional field on `Hedge` and `HedgeCandidate`. |
| `baseline_real_pay_median` on crises | Optional float on `Crisis`. |
| New flags `category_level`, `bridged_soc2000`, `sources_disagree` | Kept on the metric. All three are `MUST_MENTION`, so their `FLAG_TEXT` sentence goes in `notices`. |
| `history.json` 2007 to 2025 | `HistoryPoint[]`; `jobs_k` null before 2011. |
| `schema_version: "1.1"` | Ignored by the API. |

Also new, and not from you:

- `CareerRef` and `RecommendationOut.first_idea_candidates` for "Did you mean...?".
- A malformed SOC (not 4 digits) returns 422. A well-formed unknown SOC returns 404.
- AGENTS.md rule 11: files in `snapshots/ml/` may be up to 5 MB each. Raw data is still never committed.

Unknown future fields on ML pass-through shapes are ignored. So extra fields from your push do not break the API.

### 2.2 How `load_data()` joins your artefacts

`packages/contracts/avenir_contracts/data.py`. It calls your loader `pathfinder_ml.ML`.

| Step | Your call | Used for |
| --- | --- | --- |
| Mode and statuses | `ml.status()` | `ml_mode` in `/health`, one source status per artefact |
| Careers | `ml.occupations(demo_only=True)` | The 20 demo careers, joined with the catalogue entry by `soc2020` (`join_career`) |
| Hedges and history | `ml.hedges(soc, k=5)`, `ml.history(soc)` | Per demo career |
| Tags | `ml.tags()` | The interest checklist |
| Affinity | `ml._load("fit")["affinity"]` | Matcher scores. Private call, marked `TODO(arsenii)` (question 4) |
| Backtest | `ml._load("backtest")`, `ml.backtest_caveats()` | Windows by base year. Private call (question 4) |
| Crises and sources | `ml.crises()`, `ml.sources()` | `/crises`, `/sources` |

If a file is missing, `load_data()` skips that part and the API reports it as `missing`. Nothing crashes.

### 2.3 Manifest entries added from your section 3.3

`data/manifest.yaml` now has 8 ML sources, plus `routes_curated` (a hand-copied table, not from you).

| id | Your source | Still to fill (verify) |
| --- | --- | --- |
| `ashe_2007_2010` | ASHE Table 14, 2007 to 2010 (SOC 2000) | URL. We guessed the ONS ASHE page; the 2007 to 2010 editions may sit on a different page |
| `soc2000_soc2010` | SOC 2000 to SOC 2010 relationship tables | URL (empty) |
| `cpih` | CPIH series L522, dataset MM23 | URL (empty) |
| `soc2020_coding_index` | SOC 2020 coding index | URL (empty) |
| `dfe_ai_annex` | DfE AI annex 1 | URL (empty) |
| `ons_job_adverts` | ONS job adverts, 28 categories | URL (empty). Question 9 asks which licence covers it |
| `aps_2016_age_bands` | APS 2016 age bands, request 006998 | URL (empty) |
| `onet` | O*NET 31.0 and ESCO crosswalk | URL (empty) |

- Licences were copied from your section 3.1 (OGL v3.0 for the ONS and DfE rows, CC BY 4.0 for O*NET). Please check each.
- `licence_checked_by` is empty on all 8. Put your initials in once you have read the licence (AGENTS.md section 6).
- The URLs are yours to fill: your `SOURCE.md` files have none.

### 2.4 Codex's integration harness (PR #7)

`scripts/integration/` (see its `README.md`). It validates your PR automatically.

- It merges all branches into a temporary tree, including every `origin/arsenii/*` branch. **Name your branch `arsenii/<something>`** so it is picked up.
- It runs tests and lint, then a freeze run with `AVENIR_FREEZE=1`.
- The ML probe loads every occupation, counts the demo careers, checks every metric's flags through `join_career`, lists unknown metric keys and prints file sizes. Files over 5,000,000 bytes are marked.
- It runs at 01:00, at 08:30, and every 15 minutes through a watcher. Reports go to the shared folder.
- With the v1.1 overlay (your KATYATA `03fb482` placed over `packages/ml` and `snapshots/ml`), earlier runs loaded 412 occupations and 20 demo careers with no lost flags. The only v1.1-specific breaks were on our side and are fixed.

### 2.5 The LLM adapter's checks

`packages/adapters/avenir_adapters/llm/writer.py`. This is why we do not need `validate_explanation`.

- Every number in the text must be in the response.
- Every notice sentence must be copied verbatim.
- The words "you should" and "don't" are rejected, and so are spelled-out numbers.
- A hard 3 s limit and a circuit breaker apply. Any failed check falls back to the template text.
- No API keys exist yet. Today explanations use the template.

Your review finding (section 7.3) still matters: `employees_only` sits on most metrics. Our proposal is to put constant caveats in a card footer (open decision 3 below).

One thing to know: `FLAG_TEXT` and `MUST_MENTION` in `packages/ml/pathfinder_ml/api.py` on main are still the v1.0 versions. They do not have your three v1.1 flags. They arrive with your PR (section 4).

---

## 3. Answers to your section 10 asks

| # | Your ask | Answer and status | Owner |
| --- | --- | --- | --- |
| 1 | Matcher labels (20 texts each, 2 or 3 people) | Not scheduled yet. Yehor to ask the team tonight. Without labels fit stays "preliminary" | Yehor |
| 2 | Confirm the 20 demo careers | Open. Proposal: confirm as listed. See your answer to question 3 below | Team |
| 3 | 2008 crisis off the cards | Proposal pending the team: off the cards, kept in "how we checked" (your recommendation) | Team, Yehor to call it |
| 4 | Cost-of-living window | No proposal yet. Your recommendation: 2023 to 2025, noise filter, drop if still unstable | Team |
| 5 | Pull the plug | Proposal pending: switch off Adzuna, the LLM and your matcher service, with one badge each. Today `/demo/live` switches off Adzuna only | Yehor, Nazar |
| 6 | Track-record label | Proposal pending: "How simple rules held up" | Team |
| 7 | Close PR #2, merge your summary, accept the real push under 5 MB | Done. PR #2 closed, PR #10 merged, 5 MB rule merged in PR #4 | Yehor |
| 8 | Add missing sources to the manifest | Entries done (section 2.3). URLs, licence checks and initials left | You |
| 9 | "No lower-risk hedge" case, `evidence` copy, null group and `other` in backtest groups | Nazar's decision engine (PR #8) passes `evidence` from the candidate to the hedge. We do not know the status of the "no lower-risk hedge" case: **Nazar, please confirm**. Question 5 asks about the `balanced` group | Nazar |
| 10 | `validate_explanation` as well as the adapter's check | Not needed. The adapter check covers it (section 2.5). Do not spend time on it | Closed |
| 11 | Frontend badges and chart text | Noted for the frontend pairs: break job lines at 2021; history 2007 to 2025 (job counts from 2011); "estimate" badge on `evidence: "estimate"`; "category level"; "sources disagree"; text alternative for charts; hedges mean "closest skills"; track record means "how simple rules held up". `apps/web/` is still empty | Frontend pairs |
| 12 | Scrub `packages/ml/RUNBOOK.md` | Still to do. See the checklist in section 4 | You and Yehor |

---

## 4. Your Sunday PR: what we need and how we take it

### What we need

| Item | Detail |
| --- | --- |
| When | Sunday 08:00 to 09:30. One PR, branch named `arsenii/...` |
| Content | `packages/ml` plus real files in `snapshots/ml/` (v1.1 plus matcher plus v1.2, your section 10 plan) |
| Size | Each file in `snapshots/ml/` under 5 MB (AGENTS.md rule 11) |
| Shapes | Compatible with contract v2.1 (section 2.1). No new metric keys (your 8.4 says none are planned) |
| New flags | Add each to `FLAG_TEXT` and `MUST_MENTION` in `pathfinder_ml/api.py`. `notices_for` then picks them up with no code change. This includes the three v1.1 flags |
| Mock files | May grow beyond 20 occupations (demo careers plus hedge targets). `demo_set` stays exactly 20 |
| Values | May move. We do not hard-code them (see below) |

### After it lands

1. Codex runs the harness and posts the report (a run is due at 08:30 and every 15 minutes).
2. Yehor regenerates the frontend pack: `python -m avenir_contracts.examples`.
3. Nazar updates any tests that hard-coded sample values.
4. `AVENIR_FREEZE=1 pytest` goes green. It fails today on purpose, because sample data is still served.
5. Around 10:00 we rehearse pull the plug.

The real catalogue and routes come from Yehor's side at about 09:30, after the team fills the CSVs at 08:00.

### Pre-push checklist

- [ ] `ruff check .` is clean. This is the lint fix you promised for the import (139 findings, mostly line length).
- [ ] `pytest` is green with your files in place.
- [ ] Every file in `snapshots/ml/` is under 5 MB (`ls -l snapshots/ml`).
- [ ] No raw data under `data/raw/` is staged.
- [ ] No hostnames, machine names or local paths in `packages/ml/RUNBOOK.md` or anywhere else (your ask #12).
- [ ] Every new flag is in `FLAG_TEXT` and, if it must be said, in `MUST_MENTION`.
- [ ] `demo_set` in `occupations.json` has exactly 20 SOCs.
- [ ] Branch name starts with `arsenii/`.
- [ ] Manifest URLs and `licence_checked_by` filled, or listed in the PR text as still open.

---

## 5. Questions for you

Full text: `C:/dev/Avenir-wt/_shared/questions-for-arsenii.md` (21 questions). **Please answer inline in that file, or as a PR comment.** One or two lines is enough.

**Answer before the 08:00 push (marked MUST):**

| # | Topic |
| --- | --- |
| 1 | PR timing and branch |
| 2 | `fit.json`: real or keyword fallback |
| 3 | Final demo set of 20 |
| 13 | Look-ahead in the backtest |
| 17 | Sibling-mean imputation of ILO exposure |

**Timing and hand-off**

1. **MUST.** When will you push v1.1 (`packages/ml` plus `snapshots/ml`), and as which branch or PR?
2. **MUST.** `fit.json` is still a placeholder (`status: mock`). When does the real one land (keyword or embeddings)? If it misses the freeze, is transparent keyword affinity the fallback you want shipped?
3. **MUST.** Is the demo set final (the 20 SOCs in `demo_set`)? Our catalogue CSV and routes are keyed on it.

**Contract and API use**

4. Can you add public accessors `ML.affinity()` and `ML.backtest_years()`? `load_data()` uses `ml._load(...)` today.
5. Nazar's pick rules (eligible, ambitious, safe, balanced) are on PR #8. Will the backtest `balanced` group use them? It is null today.
6. `ml.status()["mode"]`: with real files plus a mock `fit.json`, is "mixed" the intended mode? The UI badges key off it.

**Data correctness (we show these numbers to a 17-year-old)**

7. History 2007 to 2010 is bridged from SOC 2000. How reliable is it per occupation, and should the UI dim those years beyond the flag sentence?
8. What triggers `sources_disagree` (the ILO and DfE threshold)?
9. `resilience_tech_slump` comes from ONS job adverts built on Adzuna data. Which licence covers that series, and is it in the manifest?
10. Are the licences for ILO WP140, ESCO, DfE exposure and ONS APS 2016 checked and recorded (`licence_checked_by`)?
11. Real pay is in "CPIH, April 2025 prices". Is that the right base for every series including history, and should the UI say "in today's money"?
12. Is there a test proving no look-ahead for every backtest window (AGENTS.md rule 6)?

**Codex's code-level audit** (main `227b5e9`, KATYATA `03fb482`)

13. **MUST.** `build_artefacts.py:414-417` (also `make_mocks.py:321-325`) includes future `rpg` and `jg` in `dropna()` before base-year tier quantiles. Can you freeze eligibility and cutoffs on base-year features first, then attach outcomes? A synthetic check moves career D into the top tier when only career F's future outcome goes missing.
14. `weighted_map()` returns `coverage`, but history and 10-year growth keep only `value`. What minimum observed-source coverage is required, and can coverage be carried through both SOC bridges?
15. `crosswalk_2000.py:24-29,53-62` drops the small-base `*`, treats unparseable percentages as zero, falls back to an unweighted male and female mean, and renormalises. Which flag or base-count field makes these cases visible downstream?
16. `native_relative()` gives a ratio of growth factors, not a percentage-point difference (a 20% fall against a 50% fall gives +60%, not +30 points). Which definition ships, and will the note, the contract and a numeric test agree?
17. **MUST.** `build_artefacts.py:188-193` fills missing ILO exposure with the mean of sibling occupations. Is there an approved source-based parent estimate, or should it stay missing under AGENTS rule 3? How can a user tell a sibling average from an observed parent estimate?
18. Which dependency versions and input hashes reproduce `build_artefacts.py`? It needs Parquet and SciPy, which the root dependencies do not declare. `NOW` changes per process and bootstrap randomness is global. Can the build emit a manifest, commit and seed record?
19. `boot()` returns three `None` values for fewer than five observations, and both backtest builders pass them to `math.expm1()`. Should a sparse cohort give missing interval metrics instead of ending the build? Is there a boundary test?
20. `hedges_build.py:72-74` takes `evidence` from the target occupation only. If the source is an ISCO fallback and the target has title evidence, should the hedge still show an estimate badge?
21. Ambitious and Safe masks can overlap, while `group_then` picks Ambitious first. Are group summaries intentionally overlapping portfolios, or should they partition? How should clients reconcile group counts with the single label?

---

## 6. Open decisions

Yehor confirms these with the team. Your recommendation is shown where you gave one (section 10).

| # | Decision | Proposal | Your recommendation |
| --- | --- | --- | --- |
| 1 | Pull the plug scope | Switch off Adzuna, the LLM and your matcher service, with a badge each. Today `/demo/live` switches off Adzuna only | Same (ask 5): matcher service and LLM off, keyword tagger and template take over |
| 2 | LLM for the demo | Gemini free tier through the OpenAI-compatible adapter if anyone has a key; else template only | None |
| 3 | Constant caveats (for example `employees_only`) | Card footer, not repeated in `notices` or prose | Yes (your review finding, 7.3): constant flags go on the card |
| 4 | 2008 crisis | Off the cards, kept in "how we checked" | Same (ask 3) |
| 5 | Track-record label | "How simple rules held up" | Same (ask 6) |
| 6 | Your `validate_explanation` | Not needed | You left this to Yehor (ask 10) |
| 7 | The 20 demo careers | Confirm as listed in your section 10 | Confirm as listed (ask 2) |

Not yet a proposal: the cost-of-living window (ask 4 above).
