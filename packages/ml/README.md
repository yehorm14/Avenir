# ML slice: what it delivers, how it's checked, how to use it now

Owner: **Arsenii** (`z1nare`). Folders: `packages/ml/` (code, scripts, tests, docs) and `snapshots/ml/` (artefacts the app loads).
Contract: [`CONTRACTS.md`](CONTRACTS.md). Cluster notes: [`RUNBOOK.md`](RUNBOOK.md).

## For teammates: start here

- **Build against the mocks now:** `snapshots/ml/mock/*.json`. They have the final shapes, and many values are already real (see the status column below). Real artefacts will land in `snapshots/ml/` under the same names; your code won't change.
- **Python:**
  ```python
  import sys; sys.path.insert(0, "packages/ml")
  from pathfinder_ml import ML, FLAG_TEXT, MUST_MENTION
  ml = ML()
  ml.occupation("2134")["metrics"]["pay_median"]   # value, range, source, year, confidence, flags
  ml.match_tags("I like drawing and fixing bikes")  # [{"tag": "art_drawing", ...}, ...]
  ml.fit_scores(["maths", "art_drawing"])           # {"2134": 0.3, ...}
  ml.hedges("2451")                                  # related careers
  ml.backtest(2014)                                  # "pick a past year"
  ml.status()                                        # real vs mock, for the badges
  ```
  Standard library only: no torch, no pandas, nothing to install.
- **Tests:** `PYTHONPATH=packages/ml python -m pytest packages/ml/tests -q` (19 contract tests).
- **The LLM rule:** any sentence the LLM writes about a number must mention that number's `MUST_MENTION` flags (bridged data, the 2021 code change, COVID year, employees only, estimated, sample data). `FLAG_TEXT` gives a plain sentence for each.

## What the team gets

| Artefact | Powers in the app | Status in the mock | Next |
| --- | --- | --- | --- |
| `occupations.json` | The risk and reward card: pay level and range, real pay path, jobs, demand trend, AI exposure, crisis resilience | **Real (preliminary)** for 20 demo careers. DfE exposure, tech slump and 2008 are pending | All 412 occupations; DfE check; Census and adverts once loaded |
| `history.json` | Pay and jobs charts, 2011 to 2025 | **Real (preliminary)** | Final bridge |
| `hedges.json` | The hedge career | Placeholder (same group, lower exposure) | ESCO skill overlap (M3) |
| `fit.json` | Interest checklist and fit scores | Placeholder affinities; the keyword matcher works | Matcher (M1), with keyword search as the baseline to beat |
| `backtest.json` | "Pick a past year" track record | **Real (preliminary)**: windows 2013→18, 2014→19, 2019→24 | Final tier rules, more windows |
| `crises.json` | Crisis definitions and baselines | COVID and cost-of-living **real**; tech slump and 2008 pending | Online job adverts; ASHE 2007-11 |
| `sources.json` | Sources page and provenance | Real | Grows with each source |
| `eval.json` | "How we checked" panel | Bridge and backtest probes real; the rest pending | Matcher, exposure and hedge evaluations |

## Work packages

Every package follows the same rule: **simplest version first, measured on data it never saw, and the next step ships only if it beats the previous one.**

### D0. Data pipeline (done)

- **Loaded locally:**
  - ONS ASHE Table 14 for 2011 to 2025: 11,500 rows, 369 SOC 2010 and 412 SOC 2020 occupations, about 90% with pay.
  - The ONS SOC 2010↔2020 crosswalks.
  - The SOC 2020 coding index (30,000 job titles with SOC and ISCO codes).
  - The ILO GenAI exposure index (427 occupations).
  - CPIH for real terms.
- **Scripts:** `ashe_extract.py`, `ashe_parse.py`, `crosswalk_build.py`, `ilo_parse.py`, `make_mocks.py`, plus the `probe_*.py` checks.
- **Raw data** stays in `data/` (gitignored). Only derived aggregates from open-licence sources are committed.

### M5. Track record ("pick a past year")

- **Purpose:** show how Pathfinder's ratings from past years turned out, which no other careers tool does.
- **Method:** pre-registered, naive tiers with nothing tuned to outcomes. "Ambitious then" is the top third by pay at the base year; "Safe then" is the top third by prior job growth. Outcomes are real pay growth and job growth 5 years later, with bootstrap intervals.
- **Windows:** inside the SOC 2010 era (2013→2018, 2014→2019), plus bridged windows to the present (2019→2024 for pay only). Every bridged value is flagged.
- **Probe result:** careers that were growing kept growing; jobs fell in about 30% of them, against about 50% of shrinking ones. High-pay careers had better job growth but *slower* real pay growth, partly because minimum-wage rises lifted low pay. The results are shown as they are.
- **Limits:** AI exposure can't be backtested (there's no historical index); the windows overlap; occupations with incomplete data drop out.

### M4. Demand trend

- **Method:** a robust (Theil-Sen) trend of employee job counts with a 90% interval, computed **within each coding era only** (2011-19 and 2021-25). Job counts are not comparable across the 2021 code change.
- **Robustness:** Theil-Sen down-weights one-off outliers. Example: data analysts show 95,000 in 2021, then 42,000 to 62,000 over 2022-25. The 2021 figure is a re-coding artefact, and the trend follows the 2022-25 growth.
- **Limit:** ASHE rounds job counts to the nearest thousand, and 37% of occupations have under 20,000 full-time jobs, so their trends get low confidence.

### M7. Crisis resilience

- **Purpose:** show which careers held up when the market broke. It is the career version of a drawdown.
- **Crises:** COVID (2019→2020, all-employee jobs, so furlough doesn't fake losses), the cost-of-living shock (real pay 2021→2023), the tech hiring slump (online job adverts 2022→2024, pending) and the 2008 financial crisis (ASHE 2007-2011 on SOC 2000, pending).
- **Values** are relative to the typical occupation in that crisis.
- **Limits:** ASHE's 2020 full-time counts are distorted (postal workers show −77%), so resilience uses all-employee counts and flags 2020. Small occupations are noisy.

### M2. Automation exposure

- **Primary:** the ILO 2025 index, averaged over all the international codes an occupation's job titles map to. The range shows how much those codes disagree.
- **Cross-check:** the DfE 2023 UK scores by SOC 2020 (pending download). Disagreement widens the range.
- **In-house check:** an LLM labels ESCO tasks on a published rubric, via ELM's university-hosted model or our own cluster. It validates the ILO score and is **not** shown as a separate number.
- **Probe result:** within one UK occupation, ILO scores differ by 0.12 typically (more than 0.20 for 95 occupations), but the weighted average and the dominant code differ by only 0.006. The headline number is stable; the spread is what to show.
- **Wording:** always "automation exposure, research estimate", never "this job will disappear".

### M3. Hedge career

- **Baseline:** shared skills between occupations from ESCO (weighted Jaccard overlap). Each hedge comes with the list of shared skills.
- **Check:** compare against O*NET's related occupations where a crosswalk exists. Embeddings are added only if they improve agreement.
- **Separation of roles:** the decision layer picks the hedge (most similar among lower-risk candidates); this package only provides the candidates.

### M1. Interest matcher

- **Ladder:** (1) a keyword baseline, which is already in `pathfinder_ml.match_tags`; (2) off-the-shelf embeddings (BGE-base, MIT licence) of ESCO occupation and skill text; (3) a contrastive fine-tune.
- **Rule:** each step must beat the one before on the **held-out human-labelled test set** (top-5 hit rate), or it doesn't ship.
- **Fine-tune data:** candidate interest statements are generated with ELM and reviewed by people; hard negatives are similar-looking occupations.
- **Runtime:** the app only loads `fit.json`, so the demo never depends on a GPU.

### M6. Evaluation sets (needs people)

- **Matcher test set:** 50 free-text "what I enjoy" profiles written by 2 or 3 teammates, each with 3 best-fit occupations. It is scored once, at the end. A separate development set is used for every choice along the way.
- **Explanation check:** 20 LLM explanations checked to cite only numbers in the API response.

## Modelling protocol (avoiding overfitting and silent failure)

1. **Rules are written before outcomes are seen.** Tier and threshold rules are fixed first, then measured; they aren't adjusted to improve the result.
2. **Baselines first.** Keyword search before embeddings, embeddings before fine-tuning, simple trends before anything learned. A model that doesn't beat its baseline is dropped and the result is reported.
3. **Honest splits.** Out-of-time validation for anything over time. The human-labelled test set is touched once.
4. **Intervals and confidence everywhere.** Bootstrap and Theil-Sen intervals, ONS sampling error, confidence badges and caveat flags in every artefact.
5. **Failures are published.** Null results go into `eval.json` and the README, not into a drawer.
6. **No model decides.** Models produce evidence; the picks are visible rules; the LLM only writes prose and must mention the flags.
7. **Data problems go to the team before modelling decisions.** Choices are logged in `docs/decisions.md`.

## What the probes found (17 Oct)

- **Bridging pay works; bridging job counts doesn't.** Comparing bridged 2020 with native 2021: pay ratio median 0.99, with 3.6% of occupations jumping more than 25%. For job counts, 38% jump more than 25%, because re-coding creates fake swings (e.g. secondary teachers 306,000 → 446,000 → 358,000).
- **Real pay fell for most careers from 2011 to 2025** (2025 prices): architects −16%, actuaries, economists and statisticians −15%, radiographers −13%, teachers −12%, graphic designers −11%, electricians −8%. Software developers rose 6%, and their jobs went from 129,000 to 343,000.
- **Job counts are 2.4 times noisier than pay year to year,** and they're rounded to the thousand.
- **ASHE covers employees only.** Freelance-heavy careers are under-counted. Translators share a code with authors, and that group *grew* among employees (8,000 to 15,000). The Census adds self-employed people.
- **"Finance and investment analysts" moved code** in 2021 (3534 to 2422), so part of their apparent growth is reclassification.

## Decisions taken (17 Oct)

- **Exposure:** ILO weighted over mapped codes, with the spread shown; DfE UK cross-check; the 4 unscored occupations filled from their parent group and flagged.
- **Demand:** ASHE, robust trend, within each coding era.
- **Return:** truthful. Current pay level and range, plus the real pay path; no projections.
- **Track record:** bridged to SOC 2020 and flagged everywhere downstream, including the LLM. Crises: COVID, cost of living, tech slump, 2008.
- **Self-employed:** add Census 2011 vs 2021 (England and Wales), plus Scotland 2011 vs 2022 if it exists at 4-digit level.

## Needs from others

| Need | From | Blocks |
| --- | --- | --- |
| ESCO v1.2.1 CSV, English | Arsenii (download) | Hedges, matcher |
| DfE 2023 AI exposure annex | Arsenii (download) | Exposure cross-check |
| ASHE 2007-2011 (SOC 2000), online job adverts, Census occupation tables | Arsenii (download) | 2008 crisis, tech slump, self-employed |
| ELM key, base URL, model names in `.env` | Arsenii | In-house exposure check, matcher training pairs |
| 30 minutes of labelling from 2 or 3 people | Team | Matcher test set |
| Confirm the 20 demo occupations | Team | Final fixtures |
| Adopt `CONTRACTS.md` into `docs/contracts.md` | Yehor | Contract freeze |
| Confirm the ML vs ETL split (CONTRACTS.md section 3) | Yehor and the ETL owner | Avoids duplicate work |

## Reproduce

```
python -I packages/ml/scripts/ashe_extract.py data/raw/ashe <ASHE zips...>
python -I packages/ml/scripts/ashe_parse.py data/raw/ashe data/processed
python -I packages/ml/scripts/ilo_parse.py data/raw/ilo_exposure/wp140_index.html data/processed/ilo_exposure.csv
python -I packages/ml/scripts/crosswalk_build.py data/raw data/processed
python -I packages/ml/scripts/make_mocks.py data/raw data/processed snapshots/ml/mock
python -I packages/ml/scripts/probe_ashe.py data/processed
python -I packages/ml/scripts/probe_isco.py data/raw data/processed
python -I packages/ml/scripts/probe_bridge.py data/processed data/raw/ons_cpih/cpih_index_l522.csv
```

Each raw source folder in `data/raw/` has a `SOURCE.md` with its URL and licence.

## Licences

| Source | Licence |
| --- | --- |
| ONS ASHE, CPIH, SOC crosswalks, coding index | Open Government Licence v3.0 |
| ILO WP140 exposure index | **To confirm before public release** (the repo is private now) |
| ESCO | EU open data, with attribution |
| DfE, ONS adverts, Census | Open Government Licence v3.0 |

No WRDS or other licensed data is used in this slice.
