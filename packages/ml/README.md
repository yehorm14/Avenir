# ML slice: what it delivers, how it's checked, how to use it

Owner: **Arsenii** (`z1nare`). Folders: `packages/ml/` (code, scripts, tests, docs) and `snapshots/ml/` (artefacts the app loads).
- **Team overview, plain English:** [`TEAM_UPDATE.md`](TEAM_UPDATE.md).
- **Contract:** [`CONTRACTS.md`](CONTRACTS.md) (v1.2; its first table lists what changed after the two reviews).
- **Cluster notes:** [`RUNBOOK.md`](RUNBOOK.md).
- **Labelling task:** [`eval/LABELLING.md`](eval/LABELLING.md).

## For teammates: start here

- **Real artefacts are in `snapshots/ml/`** (all 412 UK occupations, status `preliminary`). `snapshots/ml/mock/` has the 20 demo careers plus their hedge candidates (65 occupations). Same shapes in both.
- **Python** (standard library only, nothing to install):
  ```python
  import sys; sys.path.insert(0, "packages/ml")
  from pathfinder_ml import ML, FLAG_TEXT, MUST_MENTION
  ml = ML()                                          # real files, mock fallback per file
  ml.occupation("2134")["metrics"]["pay_median"]     # value, range, source, year, confidence, flags
  ml.match_tags("I like drawing and fixing bikes")   # keyword baseline
  ml.fit_scores(["maths", "art_drawing"])            # embedding-derived affinities (preliminary until the team's labels)
  ml.hedges("2451")                                  # related careers, same skill level, with shared skills
  ml.backtest(2014)                                  # "pick a past year"
  ml.status()                                        # real vs mock, for the badges
  ```
- **Tests:** `python -m pytest packages/ml/tests -q` from the repo root (61 tests; `conftest.py` sets the path). Schema checks on mock and real files, the confidence rule on every value, cross-file references, centred and placebo-gated crises, no look-ahead in the backtest tiers, the keyword tagger, the loader and the matcher service.
- **The LLM rule, with tooling:** `pathfinder_ml.explain.validate_explanation(draft, occupation)` lists every number in a draft that isn't in the record and every `MUST_MENTION` flag it fails to mention; `template_explanation(occupation)` is the deterministic fallback. Show an LLM draft only when the list is empty.

## Status of each artefact

| Artefact | Powers in the app | Status |
| --- | --- | --- |
| `occupations.json` | The risk and reward card | **Real (preliminary), 412 occupations:** pay level, range and floor/ceiling; real pay change with a range; jobs; demand relative to the typical occupation in both coding eras; ILO exposure with DfE cross-check; resilience (COVID and tech slump on cards; 2008 and cost of living fail the placebo test); under-25 share |
| `history.json` | Pay and jobs charts | **Real:** pay 2007-2025, jobs 2011-2025; every bridged year flagged, low-purity and partial-coverage years flagged too |
| `hedges.json` | The hedge career | **Real:** ESCO skill overlap at the same skill level, with each candidate's exposure difference; checked against O*NET (US) |
| `fit.json` | Interest checklist and fit | **Real (preliminary):** tag-to-career affinities from the embedding model. On the synthetic dev set it ties the hand-made table at top-3 (0.93 vs 0.90) and loses at top-1 (0.47 vs 0.70); that set is circular for the hand-made table, so the team's labels decide (see M1) |
| `career_texts.json` | Input for the optional matcher service | **Real:** ESCO texts for the 20 demo careers |
| `backtest.json` | "Pick a past year" | **Real (preliminary):** simple rules, windows 2013→18, 2014→19, 2015→20, 2019→24 (pay only); tiers from base-year data only |
| `crises.json` | Crisis definitions and baselines | **Real:** COVID, cost of living, tech slump, 2008, each with `show_on_card` and its placebo result |
| `sources.json` | Sources page | **Real:** 12 sources with licences |
| `eval.json` | "How we checked" panel | **Real:** bridge seams (with purity), backtest probe, exposure agreement (overall and within groups), hedge check against the same-group baseline, crisis placebo, matcher |

## Backtest groups: what `group_then` and `other` mean

`backtest.json` scores two simple rules fixed in advance, not the app's picks. In each window, `assign_tiers` (`scripts/ml_common.py`) builds the tiers from base-year data only, over every occupation that has both base-year inputs:

```python
"ambitious": base.pay >= base.pay.quantile(2 / 3),
"safe": base.prior >= base.prior.quantile(2 / 3),
```

- `pay`: ASHE full-time median pay in the base year (native SOC 2010 windows 2013, 2014, 2015); real pay in 2019, bridged to SOC 2020, for the 2019→2024 window.
- `prior`: change in ASHE full-time job counts from 2011 to the base year (native windows); from 2015 to 2019 (2019 window).
- Both tiers include ties at the cutoff, and they overlap: one occupation can be in both.

Each row in `occupations` carries `in_groups` (every tier it is in) and one label, `group_then`. The rule in `scripts/build_artefacts.py` is `ing[0] if ing else "other"` with `ing` in the order ambitious, safe (native windows), and `"ambitious" if amb[s] else "safe" if safe[s] else "other"` (2019 window):

| `group_then` | Meaning |
| --- | --- |
| `ambitious` | At or above the base-year pay cutoff (top third by pay then), whether or not it is also in the safe tier |
| `safe` | At or above the prior jobs-growth cutoff (top third by jobs growth then) and not in the ambitious tier |
| `other` | Scored in this window but in neither tier: below both cutoffs. It is not missing data, not a third rule and not the Balanced pick; it has no group summary of its own (these rows count only in `all`) |

`group_then` is never `balanced` or `all`; those are keys in `groups`, the summaries. `ambitious` and `safe` summarise the two (overlapping) tiers; `all` is every occupation scored in the window ("All occupations with complete data"); `balanced` is always `n: 0` with null stats ("No simple-rule version"), because the Balanced pick rule needs automation exposure, which has no history. Nazar's answer on #9 keeps it empty; the API contract also allows a group to be `null`, and the frontend skips null groups.

Rows exist only for occupations with data at both ends of the window. An occupation with a gap gets no row; it is never labelled `other`. In native windows each SOC 2020 row takes the tier and outcomes of its main SOC 2010 source code (the largest crosswalk weight), so several rows can share one source. Group `n` counts SOC 2010 occupations at the time, so it does not match the row counts. Example, 2013→2018 in `snapshots/ml/backtest.json`: 302 rows (104 `ambitious`, 65 `safe`, 133 `other`; 43 rows in both tiers), against group `n` of 85 ambitious, 88 safe and 253 all. The ML contract is [`CONTRACTS.md`](CONTRACTS.md) section 4.5.

## Work packages

Rule for every package: **the simplest version first, measured on data it never saw, and the next step ships only if it beats the previous one.**

| # | Package | Method | Check | Result so far |
| --- | --- | --- | --- | --- |
| D0 | Data pipeline | ASHE 2007-2025 across three coding eras; ONS crosswalks 2000↔2010↔2020; SOC coding index; ILO, DfE, ESCO, O*NET, CPIH, ONS adverts, APS 2016 | Seam tests at both code changes | Pay bridges cleanly (ratio ≈1.00, 4-6% of occupations off by more than 25%); job counts don't (about 50%), so they never cross a code change |
| M4 | Demand trend | Robust Theil-Sen trend with a 90% interval, within one coding era; fallback full-time → all employees → 3-digit group | Interval width sets confidence | 409 of 412 have a value; 94 use the group figure |
| M7 | Crisis resilience | Change in the crisis window minus the typical occupation's change. COVID: jobs 2019-20, own figure only with at least 50k jobs. Cost of living: real pay 2021-23. Tech slump: advert categories 2022-24. 2008: the worse of jobs and real pay, 2008-09 | Raw-count review of outliers (radiographers in COVID, architects in 2008) | Thresholds and the 2008 definition were changed after that review; all values flagged |
| M2 | Automation exposure | ILO 2025 averaged over all mapped ISCO codes, with their spread as the range; DfE as a percentile cross-check | Rank agreement | Spearman 0.78 over 409 occupations; 50 occupations flagged "sources disagree" (e.g. graphic designers: ILO counts image generation, DfE's LLM measure doesn't) |
| M3 | Hedge career | UK job titles → ESCO (refined title rule) → IDF-weighted skill vectors → weighted Jaccard; same ONS skill level only | O*NET related occupations, as an external reference | 82% of top-3 hedges are O*NET-related, against 28% for random same-level picks and 76% for "same 3-digit group"; cyber security scores 0/3 and gets a closer look |
| M1 | Interest matcher | BM25 keyword baseline → off-the-shelf embeddings (BGE-base, max cosine over ESCO text chunks) → contrastive fine-tune on 400 Gemini-generated statements (local GPU, 2 minutes) | Top-3 hit rate vs chance (0.36 with 20 careers), bootstrap CIs, paired deltas; dev = 30 synthetic profiles, test = the team's labels, scored once | **Dev only so far:** BM25 0.70, embeddings 0.90 [0.80, 1.00], fine-tuned 0.93 [0.83, 1.00]; fine-tune vs base +0.03 [0.00, 0.10], so **not shipped** (no clear gain). Through the stdlib tag chain: 0.90. Final verdict needs the team's labels |
| M5 | Track record | Pre-registered naive tiers; outcomes 5 years later; bootstrap intervals | Held-out years, nothing tuned | Growing careers kept growing (jobs fell in about 30% vs about 50%); high-pay careers had slower real pay growth (minimum-wage effect) |
| M6 | Evaluation sets | Human labels for the matcher; explanation checks | Scored once at the end | Template ready |

## Modelling protocol (avoiding overfitting and silent failure)

1. **Rules are written before outcomes are seen.** Tier, threshold and linking rules are fixed first, then measured. When a probe showed a rule was wrong (strict ISCO linking, the 2008 window), the change went to the team as a decision, not a quiet tweak.
2. **Baselines first.** Keyword search before embeddings, embeddings before fine-tuning, "same 3-digit group" as the hedge baseline.
3. **Honest splits.** Out-of-time validation for anything over time. The human test set is touched once.
4. **Intervals and confidence everywhere,** plus caveat flags, and fallbacks that are always labelled.
5. **No padding.** Missing data is filled only from a parent group or reference data, and always flagged; rows are never duplicated to bulk up samples.
6. **No model decides.** Models produce evidence; the picks are visible rules; the LLM only writes prose and must mention the flags.

### The matcher in detail (M1)

- **Runtime has two paths.** (1) Standard library: `ML.match_tags(text)` maps free text to interest tags by keyword, and `ML.fit_scores(tags)` averages the tag-to-career affinities in `fit.json`. (2) Optional service (`pathfinder_ml/service.py`, FastAPI): `POST /match` embeds the text with BGE-base and ranks careers by max cosine over their ESCO text chunks. The backend uses the service when `/health` is 200 and the tag chain otherwise, which doubles as the pull-the-plug demo.
- **Where the affinities come from.** Each tag's label and keywords are embedded as a query; the cosine against every career's chunks (max) is min-max scaled per tag. No hand-set numbers remain.
- **Training data for the fine-tune** is synthetic: 20 statements per career written by Gemini 2.5 Flash from public ESCO descriptions (`scripts/m1_gen_statements.py`). It never touches the dev or test labels.
- **Why the fine-tune isn't shipped:** on the development set it beat the base model by 0.03 with a confidence interval touching zero, and it was slightly worse at hit@1. The protocol says a step ships only when it clearly beats the previous one. The model is kept locally (`data/models/matcher-bge-ft`, gitignored) and will be re-scored on the team's labels.
- **The development set is synthetic and written by the same hand as the keyword tags,** so the keyword chain's 0.90 on it is not evidence of anything. Only the team's labels count.
- **Everything ran on the laptop GPU.** The cluster isn't needed for a 110M-parameter model; `RUNBOOK.md` stays for the optional bulk LLM job.

## Reproduce

```
python -I packages/ml/scripts/ashe_extract.py data/raw/ashe <ASHE zips 2007-2025...>
python -I packages/ml/scripts/ashe_parse.py data/raw/ashe data/processed
python -I packages/ml/scripts/ilo_parse.py data/raw/ilo_exposure/wp140_index.html data/processed/ilo_exposure.csv
python -I packages/ml/scripts/crosswalk_build.py data/raw data/processed
python -I packages/ml/scripts/crosswalk_2000.py data/raw data/processed
python -I packages/ml/scripts/esco_link.py data/raw data/processed
python -I packages/ml/scripts/hedges_build.py data/raw data/processed
python -I packages/ml/scripts/validate_hedges.py data/raw data/processed
python -I packages/ml/scripts/build_artefacts.py data/raw data/processed snapshots/ml
python -I packages/ml/scripts/m1_matcher.py texts data/raw data/processed
python -I packages/ml/scripts/m1_gen_statements.py data/processed data/processed/matcher/gen_statements.jsonl   # needs GEMINI_API_KEY in .env
python -I packages/ml/scripts/m1_train.py data/processed data/processed/matcher/gen_statements.jsonl data/models/matcher-bge-ft
python -I packages/ml/scripts/m1_matcher.py eval data/processed snapshots/ml --labels packages/ml/eval/labels_dev_synthetic.csv --split dev --model data/models/matcher-bge-ft --out data/processed/matcher/eval_dev.json
python -I packages/ml/scripts/m1_matcher.py build-fit data/processed snapshots/ml --method embed_tags --eval data/processed/matcher/eval_dev.json
```

When the team's labels exist: `m1_matcher.py eval ... --labels packages/ml/eval/labels_*.csv --split test` once, then `build-fit` with the winning method.

Python packages used: pandas, numpy, scipy, pyarrow, openpyxl, xlrd (old `.xls`), jsonschema (tests), sentence-transformers and torch (matcher only), fastapi and httpx (service and its tests).

The probes (`probe_ashe.py`, `probe_isco.py`, `probe_bridge.py`) reproduce the findings above. Each folder in `data/raw/` has a `SOURCE.md` with its URL and licence. No WRDS or other licensed data is used.

## Licences

| Source | Licence |
| --- | --- |
| ONS ASHE, CPIH, SOC crosswalks, coding index, online job adverts, APS 2016; DfE | Open Government Licence v3.0 |
| ILO WP140 exposure index | CC BY 4.0 (© ILO 2025), https://doi.org/10.54394/HETP0387; adapted (averaged over ISCO codes, mapped to SOC), so the ILO's adaptation disclaimer below applies |
| ESCO | EU open data, with attribution (verify: the ESCO download page states no licence) |
| O*NET | CC BY 4.0 (used only as a reference check) |

ILO citation, as the WP140 licence page asks: Gmyrek, P., Berg, J., Kamiński, K., Konopczyński, F., Ładna, A., Nafradi, B., Rosłaniec, K., Troszyński, M. *Generative AI and Jobs: A Refined Global Index of Occupational Exposure.* ILO Working Paper 140. Geneva: International Labour Office, 2025. © ILO. https://doi.org/10.54394/HETP0387. The required disclaimer for our adaptation:

> This is an adaptation of a copyrighted work of the International Labour Organization (ILO). This adaptation has not been prepared, reviewed or endorsed by the ILO and should not be considered an official ILO adaptation. The ILO disclaims all responsibility for its content and accuracy. Responsibility rests solely with the author(s) of the adaptation.

Details and the other source URLs: `docs/data-sources.md` and `data/manifest.yaml`.

## v1.2 review fixes (18 Oct)

Two independent reviews (data and statistics; engineering) found the arithmetic correct and the ASHE parsing exact, but several numbers trusted too much or defined badly. v1.2 fixes, with the evidence:

| Finding | Fix | Result |
| --- | --- | --- |
| Bridged pay is wrong where a new code was carved out of a catch-all old code (cyber security: a fake +29% step in 2021) | Purity of each crosswalk link; `bridged_low_purity` below 0.5 | 67 low-purity codes; their seam error is 6.4% median, 23% p90, against 3.6% and 11% for pure codes |
| April CPIH used for tax-year pay | Tax-year average | Typical 10-year real change -1.2% → +1.4% ("real pay fell since 2011" still holds) |
| `demand_trend` anchored on 2021, a distorted year | 2022-2025, relative to the typical occupation, CVs in the interval, medium at most | 403 of 412 have a value |
| Confidence didn't follow the contract (about 500 values) | One rule plus tests | 0 violations |
| Exposure ranges ignored the ILO's own spread; imputation by sibling average | sqrt(between² + within²); no imputation (missing means missing) | 402 values; 28 high, 325 medium, 49 low |
| 2008 resilience has no signal; cost of living confounded | Placebo test against ordinary years, threshold 1.25 set before running | COVID 2.02 (on cards), 2008 1.07 (off), cost of living 1.22 (off) |
| Tech slump: wrong category map, not centred, volatile categories | Reviewed SOC 2020 map (`data/category_map.csv`), de-duplicated adverts, centred, low, volatile categories null | |
| Hedge evidence one-sided, weak and twin matches | Weaker side, floor 0.05, twins dropped | O*NET agreement 83% vs 76% for "same 3-digit group" on the same 217 occupations (+7 points, 95% CI 3 to 11) |
| Backtest tiers chosen after dropping occupations with missing outcomes (look-ahead) | `assign_tiers` on base-year data only, with a test | Pay level persists strongly: 93% of top-third careers stay top third |
| Build overwrote `fit.json` and `eval.json` | Each stage owns its files; eval checks merge | |
| Keyword tagger false hits and misses | Whole words, `*` stems | "apprenticeship" no longer means coding |
| Matcher service answered junk with confident careers | Abstains below cosine 0.47 (provisional, from 9 probes) | |
