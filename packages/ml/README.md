# ML slice: what it delivers, how it's checked, how to use it

Owner: **Arsenii** (`z1nare`). Folders: `packages/ml/` (code, scripts, tests, docs) and `snapshots/ml/` (artefacts the app loads).
- **Team overview, plain English:** [`TEAM_UPDATE.md`](TEAM_UPDATE.md).
- **Contract:** [`CONTRACTS.md`](CONTRACTS.md) (v1.1).
- **Cluster notes:** [`RUNBOOK.md`](RUNBOOK.md).
- **Labelling task:** [`eval/LABELLING.md`](eval/LABELLING.md).

## For teammates: start here

- **Real artefacts are in `snapshots/ml/`** (all 412 UK occupations, status `preliminary`). The 20 demo careers are also in `snapshots/ml/mock/`. Same shapes in both.
- **Python** (standard library only, nothing to install):
  ```python
  import sys; sys.path.insert(0, "packages/ml")
  from pathfinder_ml import ML, FLAG_TEXT, MUST_MENTION
  ml = ML()                                          # real files, mock fallback per file
  ml.occupation("2134")["metrics"]["pay_median"]     # value, range, source, year, confidence, flags
  ml.match_tags("I like drawing and fixing bikes")   # keyword baseline
  ml.fit_scores(["maths", "art_drawing"])            # placeholder affinities until the matcher lands
  ml.hedges("2451")                                  # related careers, same skill level, with shared skills
  ml.backtest(2014)                                  # "pick a past year"
  ml.status()                                        # real vs mock, for the badges
  ```
- **Tests:** `PYTHONPATH=packages/ml python -m pytest packages/ml/tests -q` (28 tests: schema checks on mock and real files, plus the loader's behaviour).
- **The LLM rule:** any sentence the LLM writes about a number must mention that number's `MUST_MENTION` flags; `FLAG_TEXT` gives a plain sentence for each.

## Status of each artefact

| Artefact | Powers in the app | Status |
| --- | --- | --- |
| `occupations.json` | The risk and reward card | **Real (preliminary), 412 occupations:** pay level, range and floor/ceiling; real pay change; jobs; demand trends in both coding eras; ILO exposure with DfE cross-check; resilience in COVID, cost of living, tech slump and 2008; under-25 share |
| `history.json` | Pay and jobs charts | **Real:** pay 2007-2025, jobs 2011-2025, every bridged year flagged |
| `hedges.json` | The hedge career | **Real:** ESCO skill overlap at the same skill level; checked against O*NET (US) |
| `fit.json` | Interest checklist and fit | **Real (preliminary):** tag-to-career affinities from the embedding model; evaluated on a synthetic development set only, so the final choice waits for the team's labels (see M1 below) |
| `career_texts.json` | Input for the optional matcher service | **Real:** ESCO texts for the 20 demo careers |
| `backtest.json` | "Pick a past year" | **Real (preliminary):** windows 2013→18, 2014→19, 2019→24 (pay only) |
| `crises.json` | Crisis definitions and baselines | **Real:** COVID, cost of living, tech slump, 2008 |
| `sources.json` | Sources page | **Real:** 12 sources with licences |
| `eval.json` | "How we checked" panel | **Real:** bridge seams, backtest probe, exposure agreement, hedge check; matcher pending |

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
| ILO WP140 exposure index | **To confirm before public release** (the repo is private now) |
| ESCO | EU open data, with attribution |
| O*NET | CC BY 4.0 (used only as a reference check) |
