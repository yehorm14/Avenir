# ML slice contracts (Pathfinder)

Owner: Arsenii (`z1nare`). Code in `packages/ml/`, artefacts in `snapshots/ml/`.
Version 1.1, 17-18 Oct 2026 (1.0 was PR #9). For Yehor to fold into `docs/contracts.md` (only the integrator edits that file).

**Real artefacts (preliminary) are now in `snapshots/ml/` for all 412 occupations;** `snapshots/ml/mock/` holds the 20 demo careers in the same shapes. `ML()` reads the real files and falls back to the mocks per file. Only `fit.json` is still a placeholder.

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
| `sources_disagree` | Two independent research estimates disagree; the range is wider (v1.1) | yes | "Sources disagree" note |

### 2.4 Confidence rules

- **high:** occupation-level data, ONS sampling error at most 5%, and no flag beyond `provisional`.
- **medium:** sampling error 5 to 10%, or the value carries `bridged_soc2010` or `multi_isco`, or the interval is moderately wide.
- **low:** sampling error above 10%, `imputed_parent`, suppressed inputs, `covid_year` outliers, very wide intervals, or `mock`.

Each artefact's script implements these rules; the UI only displays them.

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
  "schema_version": "1.1", "status": "preliminary", "generated_at": "...",
  "price_base": "CPIH, April 2025 prices",
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
| `pay_median` | GBP/year | Median gross annual pay, full-time employees, latest year | 25th / 75th percentile | ONS ASHE Table 14.7a |
| `pay_p10` | GBP/year | 10th percentile (floor) | null | ASHE |
| `pay_p90` | GBP/year | 90th percentile (ceiling); often suppressed for small groups | null | ASHE |
| `real_pay_change_10y` | fraction | Real change in median pay, 2015 to 2025, in 2025 prices | null | ASHE + CPIH; 2015 is bridged |
| `jobs` | thousand jobs | Full-time employee jobs, latest year | null | ASHE |
| `demand_trend` | fraction/year | Robust (Theil-Sen) trend in jobs, 2021 to 2025 | 90% interval | ASHE |
| `demand_trend_2011_19` | fraction/year | Same, previous code era, 2011 to 2019 | 90% interval | ASHE, bridged |
| `exposure` | score 0-1 | GenAI exposure, weighted mean over mapped ISCO codes | weighted mean ± within-group spread, widened when DfE disagrees (`sources_disagree`) | ILO WP140 (2025) |
| `exposure_uk` | score 0-1 | DfE LLM exposure as a percentile rank among UK occupations (1 = most exposed); cross-check only | null | DfE 2023, bridged |
| `resilience_covid` | fraction | Change in all-employee jobs 2019 to 2020, minus the all-occupation median. Occupation's own figure only with at least 50,000 jobs, else its 3-digit group (`imputed_parent`) | null | ASHE, bridged; `extra` has the advert-category cross-check |
| `resilience_cost_of_living` | fraction | Real pay change 2021 to 2023, minus the all-occupation median | null | ASHE + CPIH |
| `resilience_tech_slump` | fraction | Change in online job adverts from the first half of 2022 to 2024 for the occupation's advert category, minus the all-adverts change (`category_level`) | null | ONS online job adverts (Adzuna) |
| `resilience_2008` | fraction | The worse of (a) all-employee jobs change and (b) real full-time pay change, April 2008 to April 2009, each minus the all-occupation median; measured in SOC 2000 and carried over | null | ASHE 2008-2009, SOC 2000, bridged twice; `extra` has both parts |
| `young_worker_share` | fraction | Share of people in the job aged 16-24 in 2016, including self-employed | null | ONS APS 2016 (ad hoc 006998), bridged |

Resilience values are relative to the typical occupation: +0.10 means 10 points better than the median occupation in that crisis.

### 4.2 `history.json`: yearly series for the charts and the LLM

```json
{ "schema_version": "1.1", "status": "preliminary", "generated_at": "...",
  "occupations": { "2134": [ {"year": 2011, "pay_median": 40250, "pay_median_real": 53604, "jobs_k": 129.0, "flags": ["bridged_soc2010"]} ] } }
```

One point per year 2007 to 2025 (v1.1). `pay_median_real` is in 2025 prices. Values can be null. Before 2011 only pay is given (`jobs_k` null; flags `bridged_soc2000` and `bridged_soc2010`). **Job counts carry `recoded_2021` from 2021 on: draw them as two separate segments.**

### 4.3 `hedges.json`: related occupations by shared skills

```json
{ "schema_version": "1.1", "status": "preliminary", "method": "esco_skill_jaccard", "generated_at": "...",
  "occupations": { "2134": [ {"soc2020": "2135", "title": "...", "similarity": 0.62,
      "shared_skills": ["..."], "evidence": "title", "why": "...", "status": "preliminary"} ] } }
```

Up to 5 candidates per occupation, sorted by `similarity` (0 to 1), all at the same ONS skill level as the occupation (never a step down). Each has `evidence`: `title` when the occupation links to ESCO through at least 3 job titles, `estimate` when it relies on the ISCO fallback (v1.1). The decision layer picks the hedge (highest similarity among candidates with lower risk); this file doesn't decide.

### 4.4 `fit.json`: interest tags and their affinity to occupations

```json
{ "schema_version": "1.1", "status": "mock", "method": "hand_mock", "generated_at": "...",
  "tags": [ {"id": "maths", "label": "Maths and numbers", "keywords": ["maths", "algebra", "..."]} ],
  "affinity": { "maths": { "2433": 0.9, "2134": 0.6 } } }
```

`tags` is the checklist the frontend shows. `affinity[tag][soc2020]` runs 0 to 1, and a missing entry means 0. Fit for a profile = mean affinity over the selected tags (`ml.fit_scores`). The real method replaces the values: zero-shot, then fine-tuned embeddings, kept only if they beat keyword search on held-out human labels.

### 4.5 `backtest.json`: the track record ("pick a past year")

```json
{ "schema_version": "1.1", "status": "preliminary", "generated_at": "...",
  "method": "...", "caveats": ["..."],
  "windows": [ {
      "base_year": 2013, "outcome_year": 2018, "horizon": 5, "coding": "SOC 2010 native",
      "flags": [], "jobs_comparable": true,
      "groups": [ {"key": "ambitious", "label": "...", "n": 84,
                    "real_pay_growth": {"median": 0.02, "low": 0.0, "high": 0.04},
                    "jobs_growth": {"median": 0.06, "low": 0.03, "high": 0.10},
                    "share_jobs_fell": 0.33} ],
      "occupations": [ {"soc2020": "2134", "group_then": "ambitious",
                        "real_pay_growth": 0.05, "jobs_growth": 0.31} ] } ] }
```

Groups are `ambitious`, `safe`, `balanced` and `all` (the baseline). A group can be null while its rule isn't fixed yet. Windows that cross 2021 have `jobs_comparable: false` and jobs fields set to null. Exposure can't be backtested (no historical index), so historical tiers use market data only; that is in `caveats`.

### 4.6 `crises.json`: crisis definitions and baselines

```json
{ "schema_version": "1.1", "status": "preliminary", "generated_at": "...",
  "crises": [ {"key": "covid", "label": "COVID-19", "window": "2019-2020",
               "measure": "...", "baseline_median": 0.0, "status": "preliminary", "flags": ["covid_year"]} ] }
```

Keys: `covid`, `cost_of_living`, `tech_slump`, `gfc_2008`. Per-occupation values live in `occupations.json` as `resilience_<key>`. `gfc_2008` also has `baseline_real_pay_median` (v1.1).

### 4.7 `sources.json`: provenance registry

`{"sources": {"ons_ashe_t14": {"name", "publisher", "url", "licence", "coverage", "years", "status", "notes"}}}`. Every Metric's `source` is a key in it. The sources page renders this file.

### 4.8 `eval.json`: how we checked

```json
{ "schema_version": "1.1", "status": "preliminary", "generated_at": "...",
  "checks": { "bridge_seam": {"status": "preliminary", "date": "2026-10-17", "summary": "...", "metrics": {}} } }
```

Check keys: `bridge_seam`, `backtest_probe`, `matcher`, `exposure_agreement`, `hedge_sanity`. Each has `status`, `date`, `summary` and `metrics`. It feeds the README and the "how we checked" panel.

## 5. Python interface (`pathfinder_ml.ML`)

| Method | Returns | Errors and edge cases |
| --- | --- | --- |
| `ML(data_dir=None)` | loader | `data_dir` defaults to env `PATHFINDER_ML_DIR`, then `snapshots/ml`; falls back per file to `snapshots/ml/mock` |
| `status()` | `{"mode": "real" or "mock" or "mixed", "artefacts": {name: {"status", "origin", "path"}}}`; `origin` is `real` (loaded from the data dir) or `mock` (fell back). `mode` is `real` only when every file came from the data dir with status final or preliminary, `mock` when every file fell back, else `mixed` | never raises |
| `occupations(demo_only=False)` | list of occupation dicts (4.1) | |
| `occupation(soc2020)` | dict or None | None for an unknown code (backend returns 404 in the envelope) |
| `history(soc2020)` | list of yearly points (4.2) | empty list if unknown |
| `hedges(soc2020, k=3)` | up to k candidates (4.3) | empty list if unknown |
| `tags()` | checklist tags (4.4) | |
| `match_tags(text, top_k=5)` | `[{"tag", "score", "matched"}]`, score 0 to 1 | deterministic keyword baseline; empty text gives an empty list; the LLM path belongs to AI/glue |
| `fit_scores(tag_ids)` | `{soc2020: score}` | `ValueError` listing any unknown tag ids |
| `backtest(base_year=None)` | one window (4.5); latest if None | `KeyError` for a year that isn't there |
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
