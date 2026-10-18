# ML slice contracts (Pathfinder)

Owner: Arsenii (`z1nare`). Code in `packages/ml/`, artefacts in `snapshots/ml/`.
Version 1.2, 18 Oct 2026 (1.1 was 17 Oct; 1.0 was KATYATA PR #9). For Yehor to fold into `docs/contracts.md` (only the integrator edits that file).

**Real artefacts (preliminary) are in `snapshots/ml/` for all 412 occupations;** `snapshots/ml/mock/` holds the 20 demo careers plus their hedge candidates (65 occupations) in the same shapes. `ML()` reads the real files and falls back to the mocks per file.

### Changes in v1.2 (after two independent reviews; shapes compatible, some definitions changed)

No metric key was added, renamed or removed. Values move, and several definitions changed: read the "Changed definition" rows.

| Change | What to do |
| --- | --- |
| Four new flags: `bridged_low_purity` and `ons_indicative_counts` (both `MUST_MENTION`), `partial_sources`, `fallback_all_employees` | `FLAG_TEXT` has the sentences; `notices_for` picks them up |
| One confidence rule for every metric (section 2.4), checked by tests over every value | Nothing; badges just become more honest (far fewer "high") |
| Changed definition: `demand_trend` is now 2022-2025 and relative to the typical occupation (2021 and 2022 were distorted by ONS occupation miscoding; ONS calls job counts indicative). `extra.absolute_trend` keeps the plain trend | Label it "jobs growing faster or slower than typical". Confidence is at most medium |
| Changed definition: `demand_trend_2011_19` is also relative to the typical occupation | Same label |
| `real_pay_change_10y` gains a 90% range (sampling plus bridging error) and `extra.purity`; low-purity codes get `bridged_low_purity` and low confidence | Show the range |
| Inflation is now CPIH averaged over the tax year (ASHE's reference period), not April. The typical 10-year real change moves from -1.2% to +1.4%. `price_base` says "CPIH, tax year 2024/25 average" | Say "in 2024/25 money" |
| `exposure` range now includes the ILO's own task spread; no more imputation (missing means missing): an occupation with under half of its job titles scored by the ILO has `value: null` | Show "missing" |
| `pay_p10`, `pay_p90` fall back to the ONS 3-digit group figure (`imputed_parent`, low) | Show the "estimated" tag |
| Crises are centred on the median occupation and face a placebo test. `crises.json` entries gain `show_on_card` and `placebo`. **COVID passes; 2008 and cost of living fail** (`show_on_card: false`): keep them off the cards, show them in "how we checked" | Read `show_on_card` |
| Changed definition: `resilience_cost_of_living` is now real pay after the shock, tax year 2022/23 to 2024/25 (the 2021 base was the furlough year). `resilience_2008` is jobs only (the "2009" pay is mostly pre-crash) | Off the cards anyway |
| `resilience_tech_slump` uses de-duplicated adverts, the same months in both years, centred; all values `low`; the four categories the ONS flagged as unreliable (Education, Marketing/PR, Transport, Travel) are `null` | Show the category name |
| Hedge items gain `exposure_delta` and `lower_exposure`; `evidence` is the weaker of the two sides; candidates below similarity 0.05 are dropped (394 of 412 occupations have candidates) | The decision layer still picks; "no lower-risk hedge" is a normal outcome |
| Backtest: tiers use base-year data only (no look-ahead, tested); `groups` is always four objects (`balanced` has `n: 0`, no simple-rule version); rows gain `in_groups`; windows gain `persistence`, `n_base_occupations`, `n_scored`; new 2015-2020 window; labelled "simple rules", not the app's picks | Label the panel "How simple rules held up" |
| `ML.affinity()`, `ML.backtest_years()`; `ML.backtest()` with no year returns the latest window with comparable job counts; `status()` reports an unreadable file as `invalid` instead of raising | Use the public accessors instead of `_load` |
| Keyword tagger: whole words only; `*` marks a stem (`draw*`). Fixes "apprenticeship" matching coding and "I enjoy helping people" matching nothing | Nothing |
| Matcher service: `/health` is 503 when no careers are loaded; `/match` abstains (`abstained: true`, empty matches) below a cosine of 0.47 | Fall back to the tag chain when it abstains |
| `eval.json` gains `crisis_placebo`; `hedge_sanity` now compares hedges with the same-group baseline on the same occupations, with intervals | Nothing |
| Every file has `schema_version: "1.2"` | |

### Changes in v1.1 (all backward compatible: additions only)

| Change | What to do |
| --- | --- |
| New metric `young_worker_share` (2016 share of workers aged 16-24, includes self-employed) | Optional card line; ignore it if you don't show it |
| New flags `category_level`, `bridged_soc2000`, `sources_disagree` | All three are `MUST_MENTION`; `FLAG_TEXT` has the sentences |
| `exposure_uk` now has values: the DfE score as a percentile rank (0-1) | Cross-check only; don't show it as a second headline number |
| `resilience_tech_slump` is now real, from job-advert categories (`category_level`) | Show the category name from `extra.adverts_category` |
| `resilience_2008` is now real: the worse of jobs and real pay, April 2008 to April 2009 | `extra` has both parts and which one is the headline |
| Hedge items gain `evidence` (`title` or `estimate`) | Show "estimate" when it says so |
| `history.json` now starts in 2007 (pay only before 2011) | Job counts start in 2011 |
| `crises.json` entries may have `baseline_real_pay_median` | Optional |
| Every file has `schema_version: "1.1"` | |

### Additions after v1.1 (still additive; same schema version)

| Change | What to do |
| --- | --- |
| `fit.json` is now real: affinities from the embedding model (`method` says which), plus an `evaluation` block (split, n, chance level, per-method hit@1, hit@3, MRR with 95% CIs, paired deltas) | Nothing required. The `status` stays `preliminary` until the team's held-out labels are scored once |
| `ML.status()` artefacts gain `origin` (`real` or `mock`), and `mode` is now decided by origin (see section 5) | Use `origin` for per-artefact badges |
| Support file `snapshots/ml/career_texts.json` (demo careers' ESCO texts) | Input for the matcher service; not a card artefact |
| **Optional matcher service** (`packages/ml/pathfinder_ml/service.py`): `POST /match {"text", "top_k"}` returns the top careers by embedding similarity plus the keyword tags, in the same envelope; `GET /health`; 503 with `error.code = "matcher_unavailable"` when the model isn't loaded | Backend: call it if `/health` is 200, otherwise use `ML.match_tags` + `ML.fit_scores`. That fallback is the pull-the-plug demo for the matcher |
| **Explanations that can't invent numbers** (`pathfinder_ml.explain`): `template_explanation(occupation)` gives deterministic prose with every `MUST_MENTION` caveat; `validate_explanation(draft, occupation)` returns a list of problems (a number not in the record, a flag not mentioned); `fmt(metric)` renders a metric with its unit | AI/glue: ask the LLM for prose from the record's numbers and `FLAG_TEXT`, run `validate_explanation`, show the draft only if the list is empty, otherwise show the template. Standard library only |

## 1. How to consume it

Two options, same data:

1. **Python (recommended for the backend):**
   ```python
   from pathfinder_ml import ML
   ml = ML()                      # reads PATHFINDER_ML_DIR, default snapshots/ml
   ml.occupation("2134")          # one occupation with all metrics
   ml.match_tags("I like drawing and fixing bikes")
   ml.fit_scores(["art_drawing", "fixing_hands_on"])
   ```
   Standard library only (no torch, no pandas). Import path: add `packages/ml` to `PYTHONPATH`, or `pip install -e packages/ml` once a `pyproject.toml` lands.
2. **Plain JSON:** read the files in section 4 directly.

**Fallback rule:** for each artefact the loader looks in `PATHFINDER_ML_DIR`, then in `snapshots/ml/mock/`. `ml.status()` reports, per artefact, whether it came from real data or the mock. The UI uses this for the "sample data" and "running on backup" badges.

## 2. Common types

### 2.1 Metric

Every number shown to a user is a Metric. Nothing is shown without its source, year and confidence.

| Field | Type | Meaning |
| --- | --- | --- |
| `value` | number or null | The number. **null means missing; never guess or fill it in the UI.** |
| `low`, `high` | number or null | The range to display around `value` (meaning is per metric; see section 4.1). |
| `unit` | string | `GBP/year`, `fraction`, `fraction/year`, `thousand jobs`, `score 0-1` |
| `as_of` | string | Data year or window, e.g. `"2025"`, `"2021-2025"` |
| `source` | string | Key into `sources.json` |
| `granularity` | string | `occupation`, `parent_group`, `major_group`, `estimate` |
| `confidence` | string | `high`, `medium`, `low` (rules in 2.4) |
| `flags` | string[] | Caveats from the vocabulary in 2.3 |
| `status` | string | `final`, `preliminary`, `mock`, `pending` (2.2) |
| `note` | string | One plain-English sentence on what the number is |
| `extra` | object | Metric-specific extras, e.g. `{"gradient": "Gradient 3", "n_isco": 4}` |

### 2.2 Status values (per file and per metric)

| Status | Meaning | UI rule |
| --- | --- | --- |
| `final` | Real data, final method | Show normally |
| `preliminary` | Real data, method not yet final | Show normally; the value may still move |
| `mock` | Placeholder with the right shape | Show a "sample data" label |
| `pending` | Source not loaded yet; `value` is null | Show "not available yet" |

### 2.3 Flags

`MUST_MENTION` flags have to appear in any prose the LLM writes about that number. `pathfinder_ml.FLAG_TEXT` gives one plain sentence per flag for templates and prompts.

| Flag | Meaning | Must mention | UI rule |
| --- | --- | --- | --- |
| `bridged_soc2010` | Value for a SOC 2020 code estimated from SOC 2010 data (years before 2021) through the ONS crosswalk | yes | Dashed line or marker for those years |
| `recoded_2021` | The series crosses the 2021 occupation-code change; job counts are not comparable across it | yes | **Break the job-count line at 2021** |
| `provisional` | ONS provisional edition (2018, 2025) | no | Small "provisional" tag |
| `covid_year` | 2020: low survey response and furlough effects | yes | Marker on 2020 |
| `employees_only` | Excludes self-employed and freelancers | yes | Footnote on the card |
| `suppressed` | ONS suppressed the estimate as unreliable | no | Show "missing" |
| `cv_high` | ONS sampling error 10 to 20 percent | no | Lower confidence badge |
| `multi_isco` | The UK code spans several international codes; exposure is a weighted mean and the range shows their spread | no | Show the range |
| `imputed_parent` | Filled from the parent occupation group | yes | "estimated" tag |
| `pending_source` | Source not loaded yet | no | "not available yet" |
| `mock` | Placeholder value | yes | "sample data" label |
| `category_level` | Measured for a broad job-advert category, not the exact occupation (v1.1) | yes | Name the category |
| `bridged_soc2000` | Value estimated from SOC 2000 data (before 2011) through two crosswalks (v1.1) | yes | Dashed line or marker |
| `sources_disagree` | The ILO and DfE percentile ranks differ by more than 0.30; the range is widened to cover both (v1.1) | yes | "Sources disagree" note |
| `bridged_low_purity` | The SOC 2010 group behind the pre-2021 figures mostly holds other jobs (purity below 0.5), so bridged values may not describe this job (v1.2) | yes | "Estimated" tag; break the pay line at 2021 |
| `partial_sources` | Less than 80% of the source weight had data (bridged codes or ILO-scored job titles) (v1.2) | no | Lower confidence badge |
| `ons_indicative_counts` | ONS says ASHE job counts are indicative, not accurate estimates (v1.2) | yes | Footnote |
| `fallback_all_employees` | Full-time counts were too sparse, so all employees are used (v1.2) | no | None |

### 2.4 Confidence rules

Each metric first gets a base level from its own evidence (the ONS sampling error of that very figure, or the width of its interval). Then one function (`ml_common.cap_confidence`) applies the flags (v1.2):

- **low** whenever the value is null or carries any of `mock`, `cv_high`, `imputed_parent`, `bridged_low_purity`, `partial_sources`, `suppressed`, `pending_source`.
- **at most medium** with any of `bridged_soc2010`, `bridged_soc2000`, `multi_isco`, `category_level`, `covid_year`, `ons_indicative_counts`, `sources_disagree`, `fallback_all_employees`.
- `employees_only`, `provisional` and `recoded_2021` don't cap (they describe the source, not the figure's reliability).
- Base levels: pay and percentiles high at ONS CV up to 5%, medium up to 10%, else low with `cv_high`. Trends high when the 90% interval is under 8 points wide, medium under 20, else low; trends on counts averaging under 20,000 or with fewer than 3 distinct values are low. Exposure high when its half-range is up to 0.08, medium up to 0.15.

`packages/ml/tests/test_api.py` checks every value in both folders against this rule.

## 3. Ownership

| Artefact or field | Owner | Notes |
| --- | --- | --- |
| Everything in `snapshots/ml/` and `packages/ml/` | Arsenii (ML) | Quantitative evidence: pay, demand, exposure, resilience, hedges, fit, backtest, evaluation |
| Display catalogue: friendly titles, descriptions, routes, entry requirements, wellbeing and stress, links | Data/ETL owner | Joined to ML artefacts on `soc2020` |
| Picks (Ambitious, Balanced, Safe), hedge choice, comparison vs first idea, roadmap | Decision layer owner | Uses ML artefacts as inputs; ML never picks |
| Endpoints, envelope, live Adzuna feed, LLM explanations | Backend and AI/glue owners | The LLM must respect `MUST_MENTION` flags |

**To confirm with the team:** the design spec (PR #8) gave pay and demand fields to the ETL slice. Since the ML pipeline already produces them from ASHE, this contract moves them into `occupations.json`. The ETL owner keeps the catalogue fields above.

## 4. Artefacts

All files have `schema_version` (semantic version), `status` (file-level, 2.2) and `generated_at` (ISO time). JSON Schemas: `packages/ml/schemas/ml_artefacts.schema.json`.

### 4.1 `occupations.json`: one quantitative profile per occupation

```json
{
  "schema_version": "1.2", "status": "preliminary", "generated_at": "...",
  "price_base": "CPIH, tax year 2024/25 average",
  "demo_set": ["2134", "3544", "..."],
  "occupations": [
    {
      "soc2020": "2134",
      "title": "Programmers and software development professionals",
      "short_title": "Software developer",
      "isco08": [{"code": "2512", "share": 0.62}, {"code": "2514", "share": 0.21}],
      "in_demo_set": true,
      "metrics": { "pay_median": { "value": 56914, "low": 42289, "high": 75794, "...": "..." } }
    }
  ]
}
```

| Metric key | Unit | `value` | `low` / `high` | Source |
| --- | --- | --- | --- | --- |
| `pay_median` | GBP/year | Median gross annual pay of full-time adult employees who have held the job for over a year, tax year 2024/25 (not starting pay) | 25th / 75th percentile (the middle half) | ONS ASHE Table 14.7a |
| `pay_p10` | GBP/year | 10th percentile (floor); the 3-digit group's figure when the occupation's own is withheld (`imputed_parent`) | null | ASHE |
| `pay_p90` | GBP/year | 90th percentile (a ceiling); rarely published for single occupations, so often the group figure (`imputed_parent`) | null | ASHE |
| `real_pay_change_10y` | fraction | Real change in median pay, tax year 2014/15 to 2024/25, in 2024/25 prices (tax-year CPIH); `extra.purity`, `extra.native_real_change_2022_2025` | 90% interval: ONS sampling error at both ends plus bridging error (6%, or 15% when purity is low) | ASHE + CPIH; 2015 is bridged |
| `jobs` | thousand jobs | Full-time employee jobs, latest year; confidence from the count's own ONS CV; `ons_indicative_counts` | null | ASHE |
| `demand_trend` | fraction/year | Robust (Theil-Sen) trend in jobs 2022 to 2025 **relative to the typical occupation** (the median occupation's path is divided out); fallback full-time, all employees, 3-digit group full-time, 3-digit group all employees; `extra.absolute_trend`, `extra.typical_occupation_trend` | 90% interval, widened to at least the sampling noise implied by ONS's CVs | ASHE |
| `demand_trend_2011_19` | fraction/year | Same, previous code era 2011 to 2019, bridged; points whose source coverage is under 80% are blanked | 90% interval | ASHE, bridged |
| `exposure` | score 0-1 | GenAI exposure, weighted mean over the ILO-scored ISCO codes the occupation's job titles map to; null when under half the titles are scored (no imputation); `extra.scored_title_share`, `extra.spread_between_codes`, `extra.spread_within_tasks` | mean ± sqrt(between-code spread² + ILO within-task spread²), widened when DfE disagrees (`sources_disagree`) | ILO WP140 (2025) |
| `exposure_uk` | score 0-1 | DfE language-model exposure as a percentile rank among UK occupations (1 = most exposed); cross-check only | null | DfE 2023, bridged |
| `resilience_covid` | fraction | Change in all-employee jobs 2019 to 2020 relative to the typical occupation. Own figure only with at least 50,000 jobs, else the 3-digit group (`imputed_parent` when the group's share is over 10%). **Passes the placebo test: on cards** | null | ASHE, bridged; `extra` has the advert-category cross-check |
| `resilience_cost_of_living` | fraction | Real pay change after the shock, tax year 2022/23 to 2024/25, relative to the typical occupation; own median only when both CVs are at most 10%. **Fails the placebo test: off cards** | null | ASHE + CPIH |
| `resilience_tech_slump` | fraction | Change in de-duplicated online job adverts, Jan-Jun 2022 to Jan-Jun 2024, for the occupation's advert category, relative to the typical occupation's category (`category_level`, always low). Null for the four categories the ONS flagged as unreliable. Not placebo-testable | null | ONS online job adverts (Adzuna) |
| `resilience_2008` | fraction | Change in all-employee jobs 2008 to 2009 relative to the typical occupation, in SOC 2000, carried over; `extra.real_pay_vs_typical`. **Fails the placebo test: off cards**, always low | null | ASHE 2008-2009, SOC 2000, bridged twice |
| `young_worker_share` | fraction | Share of people in the job aged 16-24 in 2016, including self-employed; low when the sample shows none | null | ONS APS 2016 (ad hoc 006998), bridged |

Relative values (resilience and demand) are ratios of growth factors: value = (1 + own change) / (1 + typical change) - 1, where "typical" is the median over all occupations. +0.10 means about 10% better than the typical occupation. Example: own -20%, typical -50% gives 0.8 / 0.5 - 1 = +0.60, not +30 points. `crises.json` `baseline_median` is the typical occupation's own change in that window.

### 4.2 `history.json`: yearly series for the charts and the LLM

```json
{ "schema_version": "1.2", "status": "preliminary", "generated_at": "...",
  "occupations": { "2134": [ {"year": 2011, "pay_median": 40250, "pay_median_real": 53604, "jobs_k": 129.0, "flags": ["bridged_soc2010"]} ] } }
```

One point per year 2007 to 2025 (v1.1). `pay_median_real` is in 2025 prices. Values can be null. Before 2011 only pay is given (`jobs_k` null; flags `bridged_soc2000` and `bridged_soc2010`). **Job counts carry `recoded_2021` from 2021 on: draw them as two separate segments.**

### 4.3 `hedges.json`: related occupations by shared skills

```json
{ "schema_version": "1.2", "status": "preliminary", "method": "esco_skill_jaccard", "generated_at": "...",
  "occupations": { "2134": [ {"soc2020": "2135", "title": "...", "similarity": 0.62,
      "shared_skills": ["..."], "evidence": "title", "why": "...", "status": "preliminary"} ] } }
```

Up to 5 candidates per occupation, sorted by `similarity` (0 to 1, at least 0.05), all at the same ONS skill level as the occupation (never a step down). Each has `evidence`: `title` when **both** occupations link to ESCO through at least 3 job titles, otherwise `estimate` (v1.2). `exposure_delta` is the candidate's exposure minus the occupation's; `lower_exposure` is true when it is at least 0.05 lower (v1.2). The decision layer picks the hedge (highest similarity among candidates with lower risk) and must handle "none"; this file doesn't decide. 18 occupations have no candidate.

### 4.4 `fit.json`: interest tags and their affinity to occupations

```json
{ "schema_version": "1.2", "status": "mock", "method": "hand_mock", "generated_at": "...",
  "tags": [ {"id": "maths", "label": "Maths and numbers", "keywords": ["maths", "algebra", "..."]} ],
  "affinity": { "maths": { "2433": 0.9, "2134": 0.6 } } }
```

`tags` is the checklist the frontend shows. `affinity[tag][soc2020]` runs 0 to 1, and a missing entry means 0. Fit for a profile = mean affinity over the selected tags (`ml.fit_scores`). The real method replaces the values: zero-shot, then fine-tuned embeddings, kept only if they beat keyword search on held-out human labels.

### 4.5 `backtest.json`: the track record ("pick a past year")

```json
{ "schema_version": "1.2", "status": "preliminary", "generated_at": "...",
  "method": "...", "caveats": ["..."],
  "windows": [ {
      "base_year": 2013, "outcome_year": 2018, "horizon": 5, "coding": "SOC 2010 native",
      "flags": ["provisional"], "jobs_comparable": true, "n_base_occupations": 281, "n_scored": 253,
      "groups": [ {"key": "ambitious", "label": "...", "n": 84,
                    "real_pay_growth": {"median": 0.02, "low": 0.0, "high": 0.04},
                    "jobs_growth": {"median": 0.06, "low": 0.03, "high": 0.10},
                    "share_jobs_fell": 0.33} ],
      "occupations": [ {"soc2020": "2134", "group_then": "ambitious",
                        "real_pay_growth": 0.05, "jobs_growth": 0.31} ] } ] }
```

`groups` is always four objects in this order: `ambitious` (top third by pay at the base year), `balanced` (`n: 0`, null stats: there is no simple-rule version), `safe` (top third by jobs growth before the base year) and `all`. Tiers and cutoffs use base-year data only; outcomes are attached afterwards, so a missing future value can't move anyone between tiers (tested). The tiers overlap: rows have `in_groups` (both when both apply) and `group_then` (`ambitious` wins ties; `other` = neither). Group `n` counts SOC 2010 occupations at the time; rows are today's SOC 2020 codes. Windows have `n_base_occupations`, `n_scored` and `persistence` (`pay_rank_spearman`, `top_third_by_pay_still_top_third`). Windows: 2013, 2014, 2015 (native SOC 2010) and 2019 (bridged, pay only). Windows that cross 2021 have `jobs_comparable: false` and jobs fields null. These are simple rules, not the app's picks; exposure can't be backtested (no historical index). All of this is in `caveats`.

### 4.6 `crises.json`: crisis definitions and baselines

```json
{ "schema_version": "1.2", "status": "preliminary", "generated_at": "...",
  "crises": [ {"key": "covid", "label": "COVID-19", "window": "2019-2020",
               "measure": "...", "baseline_median": 0.0, "status": "preliminary", "flags": ["covid_year"]} ] }
```

Keys: `covid`, `cost_of_living`, `tech_slump`, `gfc_2008`. Per-occupation values live in `occupations.json` as `resilience_<key>`. `gfc_2008` also has `baseline_real_pay_median` (v1.1). v1.2: every entry has `show_on_card` (boolean) and `placebo`: the cross-career spread (robust SD) in the crisis window against ordinary windows; a crisis goes on cards only when the ratio is at least 1.25. COVID 2.02 (on), 2008 1.07 (off), cost of living 1.22 (off), tech slump not testable (on, low confidence).

### 4.7 `sources.json`: provenance registry

`{"sources": {"ons_ashe_t14": {"name", "publisher", "url", "licence", "coverage", "years", "status", "notes"}}}`. Every Metric's `source` is a key in it. The sources page renders this file.

### 4.8 `eval.json`: how we checked

```json
{ "schema_version": "1.2", "status": "preliminary", "generated_at": "...",
  "checks": { "bridge_seam": {"status": "preliminary", "date": "2026-10-17", "summary": "...", "metrics": {}} } }
```

Check keys: `bridge_seam`, `backtest_probe`, `matcher`, `exposure_agreement`, `hedge_sanity`, `crisis_placebo` (v1.2). Each stage owns its checks: the main build merges into `eval.json` and never resets `matcher`. Each has `status`, `date`, `summary` and `metrics`. It feeds the README and the "how we checked" panel.

## 5. Python interface (`pathfinder_ml.ML`)

| Method | Returns | Errors and edge cases |
| --- | --- | --- |
| `ML(data_dir=None)` | loader | `data_dir` defaults to env `PATHFINDER_ML_DIR`, then `snapshots/ml`; falls back per file to `snapshots/ml/mock` |
| `status()` | `{"mode": "real" or "mock" or "mixed", "artefacts": {name: {"status", "origin", "path"}}}`; `origin` is `real` (loaded from the data dir) or `mock` (fell back). `mode` is `real` only when every file came from the data dir with status final or preliminary, `mock` when every file fell back, else `mixed` | never raises; an unreadable file has status `invalid` and an `error` string (v1.2) |
| `occupations(demo_only=False)` | list of occupation dicts (4.1) | |
| `occupation(soc2020)` | dict or None | None for an unknown code (backend returns 404 in the envelope) |
| `history(soc2020)` | list of yearly points (4.2) | empty list if unknown |
| `hedges(soc2020, k=3)` | up to k candidates (4.3) | empty list if unknown |
| `tags()` | checklist tags (4.4) | |
| `match_tags(text, top_k=5)` | `[{"tag", "score", "matched"}]`, score n/(n+1) for n matched keywords | whole-word keyword baseline (`*` = stem); empty text gives an empty list; `TypeError` for non-text, `ValueError` for negative `top_k` |
| `affinity()` | the whole `{tag: {soc2020: affinity}}` table (v1.2) | |
| `fit_scores(tag_ids)` | `{soc2020: score}` | `ValueError` listing any unknown tag ids |
| `backtest_years()` | base years with a window, oldest first (v1.2) | |
| `backtest(base_year=None)` | one window (4.5); if None, the latest window with comparable job counts (v1.2) | `KeyError` for a year that isn't there |
| `backtest_caveats()` | list of strings | show them with any window |
| `crises()` | list (4.6) | |
| `sources()` | dict (4.7) | |
| `evaluation()` | the `checks` dict (4.8) | |

`pathfinder_ml.FLAG_TEXT` and `pathfinder_ml.MUST_MENTION` back the LLM rule in 2.3.

## 6. Mapping to the design spec (PR #8, section 7)

| Spec field | This contract | Note |
| --- | --- | --- |
| `pay_now` | `pay_median` | p25 and p75 as the range |
| `pay_early` | dropped | ASHE has age bands only at 2-digit level; might return as group-level |
| `pay_ceiling` | `pay_p90` | often suppressed for small groups |
| `pay_growth_10y` | `real_pay_change_10y` | real terms, per the team's "truthful" decision |
| `pay_spread` | `pay_p10`, `pay_p90` | |
| `demand_trend` | `demand_trend`, `demand_trend_2011_19` | split by coding era |
| `shortage` | not ML | Occupations in Demand, England only (ETL) |
| `ads_now` | not ML | live Adzuna feed (backend) |
| `exposure_ilo` | `exposure` | |
| `exposure_inhouse` | `eval.json` check, not shown | in-house labels validate the ILO score; they aren't shown as a second number |
| `wellbeing`, `stress` | not ML | ETL, group-level |
| (new) | `resilience_*` | the team asked for crisis behaviour |

## 7. Versioning

`schema_version` follows semver. Adding a metric key or field is a minor bump (consumers ignore unknown keys). Renaming or removing one is a major bump, announced to the integrator first, with the mock updated in the same PR.
