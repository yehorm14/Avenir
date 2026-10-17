# Arsenii: ML slice update summary

- **Written:** Saturday 17 Oct 2026, late evening. Code freeze is Sunday 18 Oct, 11:30.
- **Author:** Arsenii (owner of `packages/ml/` and `snapshots/ml/`), written with Claude Code.
- **Asked for by:** Yehor: "push an update summary md file on github to avenir repo; include everything you have done really explicitly".
- **Where the work lives:** the KATYATA repo, branch `arsenii/ml-data` (commits `fccee2d`, `662f15c`, `03fb482`, `cb9e169`), plus work in progress that is not committed yet. Everything below ran on my laptop.
- **Numbers:** every number here comes from the project files or from the two reviews described in section 8. Anything I did not re-check tonight is marked **(verify)**.

---

## 1. Read this first

1. **The evidence layer exists for all 412 UK occupations:** pay, real pay path since 2007, demand, AI exposure, crisis resilience, hedge careers, track record and interest fit. Everything is `preliminary`. The 20 demo careers are the same files in `snapshots/ml/mock/`.
2. **Most of it is not in Avenir yet.** Avenir `main` has contract v1.0, the loader and the mocks (PR #1). The real artefacts (contract v1.1), the matcher, the matcher service and the explanation checker are in KATYATA only. I will push them to Avenir myself, as a separate PR from this one. PR #4 (open) raises the per-file limit for `snapshots/ml/` to 5 MB for this.
3. **Two independent reviews of my slice are done** (data and statistics; engineering). They found the arithmetic correct (ASHE parsing re-checked cell by cell, 0 mismatches) but found many numbers that were trusted too much, defined badly or labelled with too much confidence. Section 8 lists every finding in plain English.
4. **A fix pass, "ML v1.2", is running now.** Some fixes are done, some are in progress (section 8.3). **The v1.2 artefacts are not pushed yet and will come as a follow-up PR.** The file shapes stay compatible with contract v1.1, so nothing you build against the mocks breaks.
5. **What I need from the team** (section 10): 30 minutes of matcher labels from 2 or 3 people, confirmation of the 20 demo careers, and five decisions (2008 crisis, cost-of-living window, pull the plug, track-record label, hedge wording).
6. **Say these out loud if asked** (section 9): pay is for experienced adult employees, not starting pay; ONS calls its job counts indicative; AI exposure is a research estimate, not job loss; hedges mean "closest skills", not proven lower risk; the track record shows how simple rules held up, not how our picks did; the interest matcher has only been scored on a small synthetic set.

### 1.1 Where each piece lives today

| Piece | Where | In Avenir? |
| --- | --- | --- |
| Contract v1.0, JSON Schemas, stdlib loader `pathfinder_ml`, 8 mock files, data pipeline v1.0 and probes | Avenir `main` (PR #1, merged) | Yes |
| Same content as a draft import | Avenir PR #2 | Open and stale; Yehor wants it closed. Its description notes that imported ML code fails Avenir's lint (139 findings, almost all line length). I will fix the style in my next push |
| Contract v1.1 and real artefacts for 412 occupations (`03fb482`) | KATYATA `arsenii/ml-data` | **No** |
| Matcher, real `fit.json`, matcher service, `origin` in `status()` (`cb9e169`) | KATYATA `arsenii/ml-data` | **No** |
| v1.2 fix pass (confidence rule, purity gate, new demand window, centred crises, and so on) | My working copy, not committed | **No** |
| Explanation checker `pathfinder_ml.explain`, its tests, the advert category map script, the in-house exposure check script | My working copy, not committed | **No** |
| Contract v2.1 that adopts my v1.1 additions (additions only) | Avenir PR #4 (Yehor, draft) | Open |

---

## 2. Timeline: what I did, in order

All times are Saturday 17 Oct 2026, local time (from the commit log).

| When | What | Commit |
| --- | --- | --- |
| Before 20:43 | Probes on the raw data: how noisy are job counts and pay, does bridging between occupation-code systems work, how much does AI exposure vary inside one UK occupation, a naive backtest. These shaped the decisions in section 11 | n/a |
| 20:43 | **Contract v1.0:** artefact shapes, flags, confidence rules, Python interface, JSON Schemas, stdlib loader with mock fallback, 19 contract tests, mock files (many already with real preliminary values), data pipeline (ASHE, crosswalks, coding index, ILO, CPIH), probes, `RUNBOOK.md`, decisions | `fccee2d`, `662f15c` |
| 21:30 | **Contract v1.1:** real artefacts for all 412 occupations; hedges; four crises; DfE exposure cross-check; 2007 history start; `young_worker_share`; three new flags; hedge `evidence`; `TEAM_UPDATE.md`; 28 contract tests | `03fb482` |
| 21:59 | **Matcher:** career texts, BM25 and embedding baselines, local fine-tune (kept on the bench), real `fit.json`, optional matcher service, `origin` field in `status()` | `cb9e169` |
| Evening | Two independent reviews (data and statistics; engineering) of the committed branch | n/a |
| Night | ML v1.2 fix pass (section 8.3); delivery-status notes; explanation checker | uncommitted |

---

## 3. (a) Data sources: what is loaded, what was dropped, and why

### 3.1 Loaded and used

All raw files live in a git-ignored `data/` folder on my machine. They are not committed. Each folder has a `SOURCE.md` with its licence; 7 of the 10 have no URL yet (**verify** and fix before the sources page goes public).

| Source | Publisher | Years and coverage | Licence | Used for |
| --- | --- | --- | --- | --- |
| ASHE Table 14: 14.7a annual gross pay by 4-digit occupation and 14.7b sampling error (CV) | ONS | 2007 to 2025, 19 editions (2018 and 2025 are provisional). Employees only. Full-time and "all employees" sheets | Open Government Licence v3.0 | Pay level, range, real pay path, job counts, demand, three of four crises, track record |
| CPIH index (series L522, 2015 = 100, dataset MM23) | ONS | 1988 to 2026 | OGL v3.0 | Adjusting pay for inflation |
| Relationship tables SOC 2010 and SOC 2020 (July 2021) | ONS | Built from people coded to both systems (LFS 2014 to 2016, Census 2011) | OGL v3.0 | Bridging 2011 to 2020 data onto SOC 2020 codes |
| Relationship tables SOC 2000 and SOC 2010 | ONS | LFS Jan to Mar 2007 and Census 2001 dual coding | OGL v3.0 | Bridging 2007 to 2010 data (second step) |
| SOC 2020 Volume 2 coding index (version of 27 Aug 2026) | ONS | About 32,000 UK job titles, each with a SOC 2020 code and an ISCO-08 code | OGL v3.0 | SOC 2020 to ISCO-08 map (with shares); UK job titles for the ESCO links |
| ILO Working Paper 140, "Generative AI and Jobs: A Refined Global Index of Occupational Exposure" (Gmyrek et al., 2025) | ILO | 427 ISCO-08 occupations; mean task exposure and its spread; read from the paper's web version on 17 Oct 2026 | CC BY 4.0 according to the copyright note on the saved page (**verify**; `sources.json` in `03fb482` still says "to confirm before public release") | The headline exposure score |
| "The impact of AI on UK jobs and training", Annex 1 | DfE | 2023; 365 SOC 2010 occupations | OGL v3.0 | Cross-check of exposure, used as a percentile rank |
| Online job advert estimates (source: Adzuna), as republished by ONS | ONS | 28 job-advert categories, weekly, 2018 to 2024; discontinued Oct 2024 | OGL v3.0 | Tech-slump crisis, at category level only |
| APS 2016 age bands by 4-digit occupation (ad hoc request 006998) | ONS | UK, 2016, includes self-employed; SOC 2010; small cells suppressed | OGL v3.0 | `young_worker_share` |
| ESCO v1.2.1 | European Commission | 3,043 occupation rows (3,039 unique) and 13,939 skills | EU open data, attribution required | Hedge careers; career texts for the matcher |
| O*NET 31.0 related occupations and the ESCO to O*NET-SOC crosswalk | US Department of Labor | US occupations | CC BY 4.0 | Reference check of hedges only; never a training signal |

Models and AI services used (none of them decides anything shown to a user):

| Tool | Used for | Terms of use |
| --- | --- | --- |
| BGE-base (`BAAI/bge-base-en-v1.5`, 110M parameters) | Embeddings for the matcher | MIT licence |
| Gemini 2.5 Flash, free tier | Writing 400 synthetic training statements for the matcher fine-tune; labelling tasks for the optional in-house exposure check | Public ESCO text and synthetic text only; no personal data |

### 3.2 Not used or dropped, and why

| Wanted | What happened | Why | What replaces it |
| --- | --- | --- | --- |
| Adzuna live job-ad API | Dropped from the ML slice | It is a paid service | The free ONS advert series (above) for the tech slump. Avenir's own live adapter (Yehor, PR #5) is separate; the ML artefacts do not depend on it |
| ELM model access for bulk LLM jobs | Not used | The key needs a supervisor's approval and was not approved | Gemini free tier on public or synthetic text, plus a local model on my laptop GPU. A GPU cluster was prepared but nothing needed it |
| Census occupation counts, including self-employed | Not used in any artefact | Only broad-group files are downloaded so far (2021, England and Wales, 10 broad occupation groups by area, plus one small-area total). Four-digit counts, 2011 counts and Scotland are not loaded | An "employees only" caveat on every ASHE number. Census is a stretch goal |
| Early-career (entry) pay | Field `pay_early` dropped from the design spec | ASHE publishes pay by age only for broad occupation groups, not for individual occupations. I have not loaded that table | Pay is described as "typical pay of adult employees who have held the job over a year". It might return at group level |
| Occupations in Demand (shortage flag), wellbeing, stress | Not ML | Owned by the ETL slice (Yehor) | n/a |
| Projected pay growth | Dropped (decision, section 11) | High-pay careers grew more slowly in 2013 to 2019, so projections would mislead | "Truthful return": current pay with its range, plus the real pay path |
| Strict ISCO code linking between UK jobs and ESCO | Replaced | ONS and ESCO file 678 shared job titles under different ISCO codes | Exact job-title matching with rules (section 5.5) |
| Track record kept inside SOC 2010 only | Replaced | The team wants recent years and crisis behaviour | Bridging to SOC 2020, with every bridged value flagged |
| In-house AI-exposure scores as a second number on cards | Not shown | One headline number is clearer | ILO is the headline; the in-house check (when it runs) is only a validation in `eval.json` |
| Revised 2018 ASHE edition | Not used | I used the provisional 2018 edition. The ONS page lists both | Swap when I rerun. The revised 2025 edition is due this month, so rerun then **(verify)** |
| Any licensed or paid dataset | None used | n/a | n/a |

### 3.3 Gaps between this list and Avenir's `data/manifest.yaml` (for Yehor)

`data/manifest.yaml` lists ESCO, ASHE 2011 to 2025, the SOC 2010 and 2020 tables, SOC 2010 to ISCO-08, APS, ILO, Occupations in Demand and Adzuna. It does **not** list these sources that my pipeline uses: ASHE 2007 to 2010, the SOC 2000 and 2010 tables, CPIH, the SOC 2020 coding index, the DfE annex, the ONS job adverts, APS 2016 age bands, and O*NET. Licences are in the table above, so you can add them. AGENTS.md section 6 says every source must be in the manifest.

One correction to `docs/data-sources.md` item 3 ("no SOC 2020 to ISCO-08 file exists"): the ONS coding index gives each job title both a SOC 2020 and an ISCO-08 code. I use that to build a SOC 2020 to ISCO-08 map with shares (`crosswalk_build.py`).

---

## 4. (b) The pipeline

### 4.1 Steps (scripts in `packages/ml/scripts/`)

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `ashe_extract.py` | Takes the ONS ASHE zips, keeps only Table 14.7a (pay) and 14.7b (sampling error), one folder per year. File names are reduced to their base name so a zip cannot write outside its folder |
| 2 | `ashe_parse.py` | One long table: year, edition, SOC version, code, title, sheet, jobs (thousands), median, mean, deciles and quartiles, median CV. "x", ".." and blanks become missing. ONS quality guide for CV: up to 5% precise, 5 to 10% reasonably precise, 10 to 20% use with caution, above 20% suppressed |
| 3 | `crosswalk_build.py` | SOC 2010 to SOC 2020 composition weights (for pay) and split shares (for counts); SOC 2020 to ISCO-08 with shares |
| 4 | `crosswalk_2000.py` | The same for SOC 2000 to SOC 2010 (LFS Jan to Mar 2007, Census 2001 where the LFS base is empty). Weights are renormalised, because ONS lists only destinations above a threshold |
| 5 | `ilo_parse.py` | Reads the ILO table from the paper's web page: one row per ISCO code with gradient, mean score and standard deviation |
| 6 | `esco_link.py` | Links UK job titles to ESCO occupations (rule in 5.5) |
| 7 | `hedges_build.py` | Skill vectors and weighted Jaccard similarity; top 5 hedge candidates per occupation |
| 8 | `validate_hedges.py` | Checks hedges against O*NET related occupations (reference only) |
| 9 | `build_artefacts.py` | Builds every JSON artefact for all 412 occupations, plus the 20-career mocks |
| 10 | `m1_matcher.py`, `m1_gen_statements.py`, `m1_train.py` | Matcher texts, evaluation and `fit.json`; synthetic training statements; the fine-tune |
| Probes | `probe_ashe.py`, `probe_bridge.py`, `probe_isco.py` | Checks run before modelling; nothing is fitted to outcomes (section 5.1) |

The whole pipeline reruns in about a minute and gives the same files apart from timestamps. That is true only with my local raw data (section 9).

### 4.2 Three occupation-code systems and how I join them

ONS changed the occupation codes twice inside the period. A number for "software developer" in 2009 and in 2023 is filed under different codes.

| Years | Coding system | Number of codes |
| --- | --- | --- |
| 2007 to 2010 | SOC 2000 | 353 |
| 2011 to 2020 | SOC 2010 | 369 |
| 2021 to 2025 | SOC 2020 (the one the app uses) | 412 |

- **Pay** for a SOC 2020 code in an earlier year is the weighted mean of the medians of its SOC 2010 source codes (weights: the share of people in the new code who were coded to each old code). For 2007 to 2010 this is done in two steps, SOC 2000 to SOC 2010 to SOC 2020. Bridged values carry `bridged_soc2010` (before 2021) and `bridged_soc2000` (before 2011).
- **Job counts** are sums of (share of an old group that went to the new code) times the old count.
- **Job counts never cross a code change.** Trends stay inside one era: 2011 to 2019 (SOC 2010, bridged) and 2021 to 2025 (SOC 2020, native). Job lines on charts break at 2021.
- **Crisis windows are measured natively** (COVID in SOC 2010, 2008 in SOC 2000). Only the relative change is carried over to today's codes.
- **Fallback for sparse occupations:** full-time counts, then all-employee counts, then the ONS 3-digit parent group. Each step is flagged (`imputed_parent` for the parent group).
- **Real pay** is pay divided by CPIH, in 2025 prices. v1.1 uses the April index; v1.2 uses the tax-year average (section 8).

### 4.3 Seam tests: does bridging work?

I compared bridged values with native values on both sides of each code change. Source: `eval.json`, check `bridge_seam`.

| Seam | Series | Occupations (n) | Median ratio | Middle half (IQR) | Share outside 0.8 to 1.25 |
| --- | --- | --- | --- | --- | --- |
| 2020 to 2021 (SOC 2010 to 2020) | Pay | 360 | 0.993 | 0.95 to 1.034 | 3.6% |
| 2020 to 2021 | Job counts | 272 | 1.074 | 0.916 to 1.248 | 38.2% |
| 2010 to 2011 (SOC 2000 to 2010, all employees) | Pay | 319 | 1.004 | 0.958 to 1.053 | 6.3% |
| 2010 to 2011 | Job counts | 313 | 0.929 | 0.739 to 1.162 | 48.6% |

**Reading:** pay lines up across both seams (ratio close to 1), job counts do not. That is why pay is bridged and job counts are never joined across a change.

**What the data review added:** the "within 0.8 to 1.25" band hides the error per occupation. At the 2020 to 2021 seam the typical net error for one occupation is 4.2% and the worst tenth is 14.3% or more. It is concentrated in occupations carved out of old catch-all codes (section 8.2, finding 1). Also, part of the 2021 job-count break is general instability in the first SOC 2020 counts, not only the recode: the share of occupations whose count moved outside the 0.8 to 1.25 band in one year is 25.1% for 2021 to 2022 and 3 to 7% in 2011 to 2019.

### 4.4 Probes (run before any modelling)

| Probe | Question | Finding |
| --- | --- | --- |
| `probe_ashe.py` A | How noisy are year-on-year changes in job counts compared with median pay? | Job counts are far noisier than pay |
| `probe_ashe.py` B | A naive tier rule inside the SOC 2010 era, checked against outcomes 5 years later (no bridging) | Pay rank at the base year is negatively related to later real pay growth; prior jobs growth is weakly positively related to later jobs growth (section 5.7) |
| `probe_bridge.py` | Does bridging SOC 2010 onto SOC 2020 work? | Pay yes, jobs no (4.3) |
| `probe_isco.py` | How much does the ILO score vary inside one UK occupation? | One UK occupation spans several ISCO codes whose scores differ by 0.12 on average, so the join method matters |

### 4.5 Job title to ESCO linking (the hedge and matcher backbone)

Rule fixed on 17 Oct before I looked at any hedge:

1. An exact match to an ESCO **preferred** label links across ISCO codes.
2. An exact match to an ESCO **alternative** label links only within the same ISCO code. A link supported by a single alternative-label match is dropped.
3. A SOC group left with fewer than 3 links gets every ESCO occupation under its main ISCO code, marked `isco_fallback`. Downstream this is shown as an **estimate**.

---

## 5. (c) Work packages: method, result, status

Rule for every package: the simplest version first, measured on data it never saw, and the next step ships only if it beats the previous one.

| # | Package | Status in `03fb482`/`cb9e169` | Headline result | Review verdict | v1.2 |
| --- | --- | --- | --- | --- | --- |
| D0 | Data pipeline | Done, real | Pay bridges, job counts do not | Parsing exactly right; bridging error hidden for carved-out codes | Purity gate in progress |
| R | Expected return (pay, real pay path) | Real, preliminary | Real pay fell for most careers since 2011 | Deflator timing wrong; ceiling missing for 377 of 412 | Deflator done; rest in progress or planned |
| M4 | Demand trend | Real, preliminary | 409 of 412 have a value | Window includes distorted years | New window in progress |
| M7 | Crisis resilience (4 crises) | Real, preliminary | COVID has real signal; 2008 has none | See 5.3 | In progress |
| M2 | Automation exposure | Real, preliminary | ILO and DfE rank-correlate at 0.777 | Ranges too narrow | In progress |
| M3 | Hedge careers | Real, preliminary | 82.1% of top-3 hedges are O*NET-related (233 of 412 occupations) | Partly circular; evidence label one-sided | Partly done |
| M1 | Interest matcher | Real, preliminary | Dev set only; final score needs the team's labels | Evaluation too small to show a gain | Labels needed |
| M5 | Track record | Real, preliminary, 3 windows | High pay persists; high pay grew more slowly | Tiers are simple rules, not our picks | Relabel in progress |
| M6 | Evaluation sets | Template ready | n/a | Needs numeric ship rule and second labeller | Labels needed |
| Q | Quality layer (flags, confidence, sources page, eval file) | Real | n/a | Confidence does not match the contract in 9 ways | Single rule in progress |

### 5.1 Expected return: pay now, range, real pay path

- **What the user sees:** pay now and its range; the real (inflation-adjusted) pay path since 2007.
- **Method:** medians and percentiles from ASHE for full-time employees, latest year; no projections. `pay_median` has p25 and p75 as its range; `pay_p10` is the floor and `pay_p90` the ceiling. `real_pay_change_10y` is the real change in median pay from 2015 to 2025 in 2025 prices (2015 is bridged). `history.json` has one point per year, 2007 to 2025, nominal and real. `young_worker_share` is the share of people in the job aged 16 to 24 in 2016, including self-employed.
- **Result:** real pay fell for most careers since 2011, and that survives the deflator fix (2011 to 2025: about -2.7% typical with the April index, -2.6% with the tax-year index; about 60% of occupations negative either way, per the data review).
- **Review found:**
  - The inflation index used April prices, but ASHE annual pay is for the tax year ending 5 April. The 2015 to 2025 price rise is +37.8% on the April basis and +34.4% on the tax-year average. That changes the typical 10-year real pay change from -1.15% (53.2% of occupations negative) to +1.38% (44.4% negative). **Done in v1.2** (re-measure after rebuild, **verify**).
  - `pay_p90` (ceiling) is missing for 377 of 412 occupations and `pay_p10` for 192. Only 4 of the 20 demo careers have a ceiling (2134, 2133, 5241, 2313). 100 `pay_median` values have a range with p75 missing.
  - `real_pay_change_10y` has no range, and is wrong for some carved-out codes (see 8.2, finding 1).
  - ASHE annual pay covers adult-rate employees who have held the same job for over a year. It is not entry pay.
- **Plan:** fall back to the wider group's ceiling (would fill about half of the gaps, flagged `imputed_parent`) and show the 75th percentile as "the top quarter earn more than". Planned, not confirmed built **(verify)**.

### 5.2 Demand: is the job growing?

- **Method:** a robust (Theil-Sen) trend in job counts with a 90% interval, inside one coding era. `demand_trend` covers 2021 to 2025; `demand_trend_2011_19` covers the earlier era. Interval width sets the confidence.
- **Result:** 409 of 412 occupations have a value; 94 of them use the 3-digit group figure.
- **Review found:**
  - ONS says its job counts "are not reliable estimates" and are indicative. For 2021 and 2022 the ONS notes add that the survey data used for weighting had occupation-miscoding. Neither caveat was on the cards.
  - 2021 sits high and drags every 2021 to 2025 trend down. Refitting on 2022 to 2025 moves the typical trend from +1.8% a year to +4.8% a year, flips the sign for 15% of occupations and changes the published value by more than 3 points a year for 53%.
  - Examples: architects, counts in thousands 38, 31, 30, 30, 30, published -2.4% a year, against -0.5% a year from 2022. Data analysts 95, 42, 47, 55, 62.
  - ONS publishes a sampling error for every job count; the parser threw it away. For 156 of the 312 published full-time counts it is above 10%.
  - Small, rounded counts give intervals that collapse to a point (some are width zero) yet were rated "high". 77 of 272 "high" trends in 2011 to 2019 have an average count under 15 thousand.
  - Past and recent trends correlate at only 0.15. The 2011 to 2019 slope describes the past well (split-half rank correlation 0.80) but does not predict.
- **v1.2 (in progress):** trend on 2022 to 2025 measured against the typical occupation (cancels year effects), confidence capped at medium, job sampling errors carried into the interval, a new caveat flag, and the card wording "recent change in employee jobs".

### 5.3 Crisis resilience: how careers held up in four shocks

Each value is relative to the typical occupation: +0.10 means ten points better than the median occupation in that crisis. (v1.1 does not always achieve that centring; see the table.)

| Crisis | Definition | Window | Source | Review verdict | Plan |
| --- | --- | --- | --- | --- | --- |
| COVID-19 | Change in all-employee jobs 2019 to 2020 minus the median occupation. Own figure only if the occupation has at least 50,000 jobs, else its 3-digit group (`imputed_parent`). Measured in SOC 2010 | 2019 to 2020 | ASHE; advert category cross-check in `extra` | **Passes a placebo test:** dispersion across occupations that year is 0.118, against 0.052 to 0.082 in ordinary years | Keep |
| Cost of living | Real pay change minus the median occupation | 2021 to 2023 | ASHE + CPIH | Tangled with the COVID rebound (the base year is the furlough year; rank correlation with the COVID metric -0.32). No noise filter: 96 of 359 own values have sampling error above 10%. Median baseline overstated by about 3 points | Move to 2023 to 2025 with the noise filter, or drop (**team decision**) |
| Tech slump | Change in online job adverts from the first half of 2022 to 2024 for the occupation's advert category, minus the all-adverts change. Category level (`category_level`) | 2022 to 2024 | ONS job adverts | The category rules used old SOC 2010 numbering: 22 SOC 2020 codes silently fell into "Other / general" and about 30 more were wrongly assigned (about 50 of 412 wrong). Not centred (median -14.5%). Education category +105.5% for 13 occupations including the demo teacher. ONS flags Education, Marketing/PR and Transport (early 2023) and Travel (Sept 2023) as volatile | New reviewed SOC 2020 category map **done**. De-duplicated adverts, centring, "low" confidence and flags for unreliable categories in progress |
| 2008 crash | The worse of (a) all-employee jobs change and (b) real full-time pay change, April 2008 to April 2009, each minus the median. Measured in SOC 2000 and bridged twice | 2008 to 2009 | ASHE 2008 and 2009 | **Fails the placebo test:** dispersion that year (jobs 0.063; pay 0.026) is no bigger than ordinary years (0.052 to 0.082; 0.021 to 0.030). The two parts are uncorrelated (0.018), "worse of" mostly picks the noisier part, the median is -2.0% with only 23% positive, and "April 2009" annual pay is the 2008/09 tax year, mostly before the crash | **Keep in the file, off the cards,** shown under "how we checked" as an honest negative result (**team decision**) |

Honesty note: the COVID job-count threshold (20,000 changed to 50,000 jobs) and the 2008 definition were changed after I looked at outliers (radiographers -16% in COVID at the lower threshold; architects up by 2010 under jobs-only). They are decisions made after seeing outcomes, so I do not call them pre-registered.

### 5.4 Automation exposure (research estimate)

- **Method:** the ILO WP140 (2025) score for each ISCO code, averaged over all ISCO codes mapped to the UK occupation, weighted by how many coding-index titles map to each. `value` is the weighted mean; the range is the spread between codes. DfE 2023 exposure is added as a percentile rank (`exposure_uk`), a cross-check only. When the two disagree strongly the range widens, the flag `sources_disagree` is added and confidence goes to low.
- **Result:** rank correlation between ILO and DfE is 0.777 over 409 occupations. 50 occupations carry `sources_disagree`. Among demo careers, graphic designers (2142: ILO percentile 0.854, DfE 0.484) and chartered surveyors (2454: 0.782 and 0.455) disagree by more than 30 points; the ILO counts image generation and the DfE measure does not.
- **Review found:**
  - The 0.777 is driven by differences between broad job groups. Within a 1-digit group it is 0.54, within a 2-digit group 0.47. "Two independent sources" is generous; both are language-and-task exposure measures. I now say "two methods".
  - The range ignored the ILO's own task-level spread. 68 of 412 ranges had zero width and were rated "high"; 227 `multi_isco` values were rated "high" though the contract caps them at medium.
  - ISCO codes without an ILO score were dropped silently, so a few UK occupations rest on a sliver of their job titles (for example SOC 3311 on 1 of 57 titles). 11 groups have under 80% of titles scored and 6 under 50%.
  - Four manager groups (1161, 1225, 1252, 1253) are imputed from siblings; they are flagged `imputed_parent` and low.
- **v1.2 (in progress):** range = mean plus or minus the combined between-code and within-code spread (using the ILO's standard deviation), confidence from range width and scored share.
- **Optional in-house check (paused):** an LLM labels the ESCO skills of each demo career with the Eloundou et al. rubric (E0 none, E1 direct, E2 with extra software) and compares the result with the ILO score. It is not shown on cards. It is paused because some skill lists are noisy (CAD technicians were given programming languages). First in the cut order if time runs out. Results: none yet **(verify)**.
- Wording rule (AGENTS.md rule 7): "Automation exposure (research estimate)". Exposure is not job loss.

### 5.5 Hedge careers

- **What the user sees:** "a related job that uses many of the same skills".
- **Method:** each SOC group gets a skill vector from its linked ESCO occupations (weight = link weight times 1.0 for essential or 0.5 for optional skills times IDF, so near-universal skills like teamwork count little). Similarity is weighted Jaccard: sum of minimums over sum of maximums. Up to 5 candidates per occupation, all at the same ONS skill level (never a step down; without this, civil engineer led to construction trades). Each has `shared_skills`, a similarity and an `evidence` label: `title` when the occupation links to ESCO through at least 3 job titles, `estimate` when it relies on the ISCO fallback.
- **Check against O\*NET (US):** the share of my top-3 hedges that O\*NET lists as related. 233 of 412 occupations can be checked. Result: **82.1%**, against 27.5% for random picks at the same level and 76.2% for "any job in the same 3-digit group". Demo careers: 83.3%; cyber security (2135) scores 0 of 3.
- **Review found:**
  - The check is partly circular: 33.0% of evaluated pairs share a linked ESCO occupation with the source, and those pairs score 99.6%. Without them the hit rate is 73.5% against 26.3% for matched random picks. The lift over random is real; 82% is inflated by about 8 points.
  - On the same 227 occupations the gain over the sibling baseline is +5.6 points (95% interval 1.8 to 9.3). The 28% baseline alone, as quoted in the team update, oversells it.
  - 177 of 411 source occupations (43%) rest on the ISCO fallback and cannot be validated. The `evidence` label described only the candidate: 458 of 885 candidate rows from those sources were still labelled `title`. This includes the demo career 3544 (Data analyst).
  - No similarity floor: 342 of 2,055 candidate rows are below 0.05; 12 are exactly 1.0 (ISCO twins).
  - Hedge exposure tracks the source's exposure closely (rank correlation 0.84). Only 27.5% of occupations have any candidate with exposure at least 0.10 lower. Demo careers 2142, 2453 and 5241 have none. Florists (5443) have no hedges at all. So the file means "closest skills", not "lower risk".
  - Four ESCO URIs are duplicated, which double-weighted 9 link rows.
- **v1.2:** `evidence` now takes the weaker of the two sides (**done**); similarity floor (**done**); duplicate ESCO URIs removed (**done**). The decision layer must handle "no lower-risk hedge available".

### 5.6 Interest matcher (M1): from keyword search to embeddings

- **What the user sees:** the interest checklist and free text turn into fit scores for careers. There are 16 interest tags: maths, art_drawing, design, computers_coding, data, building_spaces, engineering_making, fixing_hands_on, electricity_energy, science_health, helping_people, teaching_explaining, money_business, security_puzzles, writing_language, outdoors_maps.
- **Methods compared, fixed before looking at results:** `random` (chance), `keyword_tags` (the stdlib chain as it was shipped), `bm25` (lexical search of the profile text against each career's ESCO text), `embed` (BGE-base, score = maximum cosine over the career's text chunks), `embed_tags` (the runtime chain with an embedding-derived affinity table), `embed_ft` (fine-tuned embeddings), `embed_ft_tags`.
- **What ships:** `fit.json` with tag-to-career affinities from `embed_tags`. Each tag's label and keywords are embedded as a query; the cosine with every career's text chunks (maximum) is scaled 0 to 1 per tag. No hand-set numbers remain. The runtime stays standard-library only.
- **Fine-tune:** contrastive training (in-batch negatives; batches built from careers in the same 2-digit SOC group so negatives are hard) on 400 synthetic statements, 20 per demo career, written by Gemini 2.5 Flash from public ESCO text without naming the job. It ran on my laptop GPU in about 2 minutes. The model is kept locally and is gitignored.
- **Development-set results** (30 synthetic profiles, 20 careers, chance for hit@3 is 0.362; hit@3 means at least one labelled career is in the top 3):

| Method | hit@1 | hit@3 | hit@3 95% interval | MRR |
| --- | --- | --- | --- | --- |
| `keyword_tags` (hand-made table) | 0.700 | 0.900 | 0.767 to 1.000 | 0.806 |
| `bm25` | 0.467 | 0.700 | 0.533 to 0.867 | 0.617 |
| `embed` | 0.767 | 0.900 | 0.800 to 1.000 | 0.847 |
| `embed_tags` (shipped in `fit.json`) | 0.500 | 0.900 | 0.767 to 1.000 | 0.693 |
| `embed_ft` | 0.700 | 0.933 | 0.833 to 1.000 | 0.819 |
| `embed_ft_tags` | 0.467 | 0.867 | 0.733 to 0.967 | 0.661 |

  Paired differences in hit@3: every method beats BM25 by 0.17 to 0.23 (the `embed_ft_tags` interval touches zero). The fine-tune beats the base embeddings by only +0.033 (interval 0.000 to 0.100) and loses at hit@1, so **the fine-tune is not shipped**; it is re-scored once on the team's labels.
- **Decision made:** ship the base embedding model, not the fine-tune (`docs/decisions.md`).
- **Review found, honestly:**
  - The development set is synthetic and written by the same hand as the keyword tags, so the keyword chain's 0.90 shows nothing. A constant predictor that always names the three most-labelled careers scores 0.50 on these 30 rows (best constant triple 0.57), so 0.90 is less impressive than it looks.
  - By my own rule ("ships only if it beats the previous step") the swap from the hand-made table to `embed_tags` is not earned yet: same hit@3 (0.90), lower hit@1 (0.50 against 0.70). The team's labels decide.
  - Affinities are scaled over the 20 demo careers only, so adding or removing a career changes every value, and the other 392 occupations have no affinity (missing is treated as 0).
  - Sample size: 60 labelled rows give about 36 test rows, which is plus or minus 15 points at 0.7. The split is a hash of the profile id, not grouped by writer.
  - The keyword matcher matched "app" inside "apprenticeship", and "I enjoy helping people" matched nothing (section 7.1).
- **Open (suggestions from the engineering review, not yet adopted):** a numeric ship rule fixed in advance (for example paired interval above 0 and gain of at least 0.10), a second labeller on part of the rows, and scoring the zero-shot methods on all rows.
- **Runtime paths:** (1) standard library: `ML.match_tags(text)` then `ML.fit_scores(tags)`; (2) the optional matcher service (7.2). The fallback between them is also the pull-the-plug demo for the matcher.

### 5.7 Track record: "pick a past year"

- **Method:** fixed rules written before the outcome numbers: at a base year, occupations are cut into thirds by pay level and by prior jobs growth ("ambitious" is the top pay third). Outcomes are measured 5 years later with bootstrap intervals. Three windows: **2013 to 2018** and **2014 to 2019** (native SOC 2010, pay and jobs) and **2019 to 2024** (pay only; job counts are not comparable across the 2021 change). Groups are `ambitious`, `safe`, `balanced` (empty for now) and `all`. Exposure cannot be backtested because no historical index exists.
- **Results** (`eval.json`, `backtest_probe`): rank correlation between pay level at the base year and real pay growth over the next 5 years is **-0.245** (2013) and **-0.390** (2014): high-pay careers grew more slowly, because the minimum-wage rises lifted the bottom of the pay scale (the data review confirmed this). Rank correlation between prior jobs growth and later jobs growth is **0.149** and **0.147**: growing careers tended to keep growing. My README summarised this as "jobs fell in about 30% vs about 50%".
- **What I should also report (data review):** pay rank persists. 93.6% (2013) and 90.7% (2014) of the top third by pay at the base year were still in the top third 5 years later (91 to 94% in my notes). That is the stronger track record.
- **Review found:**
  - The tiers are naive rules, not Ambitious, Balanced and Safe as the product picks them. "How our ratings held up" overstated it. "Pre-registered" is not literally true: I had seen probe results first.
  - The evidence for "growing careers kept growing" is weak: correlations about 0.15 (p about 0.02), and high pay predicts not-falling about as well.
  - Only survivors are scored: 10.0% (28 of 281) and 11.4% (31 of 271) of base-year occupations lose their outcome.
  - Window 1 ends on the provisional 2018 edition and is not flagged `provisional`.
  - The windows overlap by 80% so there are at most two independent ones.
  - Integration traps: `groups` always contains a null (`balanced`), so `groups.map(g => g.key)` fails; `group_then` can be `"other"` (undocumented); group counts differ from row counts (85 against 104 and 64 in 2013, because of ties and SOC 2010 against 2020 counts); `ml.backtest()` with no year returns the pay-only 2019 to 2024 window.
- **v1.2:** relabel as "how simple rules held up" (in progress), add pay-level persistence, fix the group list, document `other`, add `ml.backtest_years()`. A 2015 to 2020 window (the year in the demo script) is planned, not built **(verify)**. Nazar's pick rules (PR #8, "for Arsenii: pick rules for backtest groups") could be backtested if historical inputs exist; I have not done this and will say so before the freeze.

### 5.8 Evaluation sets and the "how we checked" panel

- **Matcher test set:** `eval/LABELLING.md` and `eval/labels_template.csv`. 2 or 3 people write about 20 "what I enjoy" texts each (varied voice, a few hard ones, no job titles) and pick the 3 best of the 20 demo careers by SOC code. A seeded script splits rows 40% development and 60% test (by a hash of the profile id). The test split is scored **once**, at the end. Headline metric: top-3 hit rate against chance, with bootstrap intervals and paired differences.
- **Development labels so far:** `eval/labels_dev_synthetic.csv` (30 synthetic profiles, AI-written). They are development only.
- **`eval.json`** holds five checks: `bridge_seam` (4.3), `backtest_probe` (5.7), `exposure_agreement` (5.4), `hedge_sanity` (5.5) and `matcher` (5.6). The review notes that re-running `build_artefacts.py` on its own overwrites the matcher check and `fit.json` with placeholders; I am separating stage outputs **(verify fixed)**.

### 5.9 Quality layer: flags, confidence, sources page

- **Metric shape (every number):** `value`, `low`, `high`, `unit`, `as_of`, `source`, `granularity`, `confidence`, `flags`, `status`, `note`, `extra`. A missing value is `null`; it is never guessed. Status is `final`, `preliminary`, `mock` or `pending`.
- **Confidence rule in the contract (2.4):** high = occupation-level data, ONS sampling error at most 5%, no flag beyond `provisional`; medium = sampling error 5 to 10%, or bridged, or multi-ISCO, or moderate interval; low = sampling error above 10%, imputed from parent, suppressed inputs, COVID-year outliers, wide intervals, or mock.
- **Review found:** the build scripts do not implement that rule. About 500 values (499) were rated higher than the contract allows, including 272 `demand_trend_2011_19` values with `bridged_soc2010` rated high and 227 `exposure` values with `multi_isco` rated high; 34 null `real_pay_change_10y` values are rated medium; `jobs`, `pay_p10` and `pay_p90` inherit the median pay's sampling error instead of their own; the fallback from full-time to all-employee counts is recorded only in free text; parent-group blends under half the weight are not flagged. Only about 4 of 14 metrics carry any range. By the letter of the rule nothing could be "high", because every ASHE metric carries `employees_only`.
- **v1.2 (in progress):** one confidence function written from the contract, a flag for any parent share above 10%, and a test over the JSON that checks the rule for every value.
- **Sources page data:** `sources.json` lists 12 entries; 11 are loaded and Census is pending. The CPIH note ("April values, the ASHE reference month") is wrong for annual pay and is being corrected.

---

## 6. (d) Artefacts in `snapshots/ml/` and what each powers

All files carry `schema_version` (1.1) and a file-level `status`. The 20 demo careers are also in `snapshots/ml/mock/` in the same shapes. Avenir's loader (`avenir_contracts.load_data()`) joins these with Yehor's catalogue and routes into 20 careers. The largest file is `occupations.json` (3.2 MB for 412 occupations, from PR #4); all files stay under 5 MB.

| File | Contents | Powers in the app | Status |
| --- | --- | --- | --- |
| `occupations.json` | 14 metrics for each of 412 occupations: `pay_median`, `pay_p10`, `pay_p90`, `real_pay_change_10y`, `jobs`, `demand_trend`, `demand_trend_2011_19`, `exposure`, `exposure_uk`, `resilience_covid`, `resilience_cost_of_living`, `resilience_tech_slump`, `resilience_2008`, `young_worker_share`; ISCO mapping; `demo_set` | The risk-and-reward card: pay and range (return), demand and resilience (market risk), exposure (disruption risk), confidence badges | Real, preliminary |
| `history.json` | Yearly points 2007 to 2025: nominal and real median pay; job counts from 2011; flags per point | Pay and jobs charts; text for the LLM. Break job lines at 2021 | Real, preliminary |
| `hedges.json` | Up to 5 candidates per occupation: similarity, shared skills, `evidence`, `why` | The hedge panel (the decision layer picks the hedge) | Real, preliminary |
| `fit.json` | 16 interest tags with keywords, tag-to-career affinities for the 20 demo careers, and an `evaluation` block | The quiz: interests to fit scores | Real, preliminary; final choice waits for the team's labels |
| `career_texts.json` | ESCO texts for the 20 demo careers | Input for the optional matcher service | Real; support file, not a card artefact |
| `backtest.json` | Three windows with tier groups, row-level outcomes, caveats | "Pick a past year" | Real, preliminary |
| `crises.json` | The four crisis definitions, windows and baselines | Crisis badges; explanations | Real, preliminary |
| `sources.json` | 12 sources with licence, coverage, years | The sources page | Real |
| `eval.json` | Five checks: bridge seam, backtest probe, exposure agreement, hedge sanity, matcher | The "how we checked" panel | Real, preliminary |

Mapping to the investment idea (from the team overview):

| Card row | Idea | Comes from |
| --- | --- | --- |
| Fit | Suitability | `fit.json` plus the decision layer's eligibility gate |
| Pay now, range, ceiling; real pay path | Expected return | `occupations.json`, `history.json` |
| Demand trend; crisis resilience | Market risk | `occupations.json` |
| Automation exposure | Disruption risk | `occupations.json` |
| Confidence badges, caveats | Forecast uncertainty | Every metric |
| Hedge career | Diversification | `hedges.json` candidates; the decision layer picks |
| Pick a past year | Track record | `backtest.json` |

Flags (the LLM must mention the ones marked "yes" when it writes about that number; `FLAG_TEXT` has one plain sentence each):

| Flag | Meaning | Must mention |
| --- | --- | --- |
| `bridged_soc2010` | Estimated from SOC 2010 data (years before 2021) | yes |
| `bridged_soc2000` | Estimated from SOC 2000 data (before 2011), two crosswalks | yes |
| `recoded_2021` | Job counts are not comparable across the 2021 code change | yes |
| `provisional` | ONS provisional edition (2018, 2025) | no |
| `covid_year` | 2020: low response and furlough effects | yes |
| `employees_only` | Excludes self-employed and freelancers | yes |
| `suppressed` | ONS suppressed the estimate | no |
| `cv_high` | ONS sampling error 10 to 20% | no |
| `multi_isco` | The UK code spans several international codes; the range shows their spread | no |
| `imputed_parent` | Filled from the parent occupation group | yes |
| `pending_source` | Source not loaded yet | no |
| `mock` | Placeholder value | yes |
| `category_level` | Measured for a broad advert category, not the exact occupation | yes |
| `sources_disagree` | Two research estimates disagree; the range is wider | yes |

---

## 7. (e) Code: loader, matcher service, explanation checker, tests

### 7.1 The loader `pathfinder_ml.ML` (standard library only)

Folder `packages/ml/pathfinder_ml/`. Import path: add `packages/ml` to `PYTHONPATH` or install the repo (Avenir's `pyproject.toml` includes `pathfinder_ml*`). Nothing to `pip install`.

| Method | Returns |
| --- | --- |
| `ML(data_dir=None)` | Loader. Reads `PATHFINDER_ML_DIR`, default `snapshots/ml`; falls back **per file** to `snapshots/ml/mock` |
| `status()` | Per artefact: status, `origin` (`real` or `mock`), path; and `mode` (`real`, `mock` or `mixed`). Never raises. This is what the "sample data" and "running on backup" badges read |
| `occupations(demo_only=False)`, `occupation(soc)` | Occupation profiles; `None` for an unknown code (the API returns 404) |
| `history(soc)`, `hedges(soc, k=3)` | Yearly series; up to k hedge candidates |
| `tags()`, `match_tags(text, top_k=5)`, `fit_scores(tag_ids)` | Interest checklist; deterministic keyword matcher; mean affinity per career (`ValueError` listing unknown tags) |
| `backtest(base_year=None)`, `backtest_caveats()` | One window (latest if none); caveats to show with it |
| `crises()`, `sources()`, `evaluation()` | Crisis definitions, source registry, `eval.json` checks |

`pathfinder_ml.FLAG_TEXT` and `pathfinder_ml.MUST_MENTION` back the LLM rule. Avenir's `notices_for` reads them.

Known issues from the engineering review (`status()` now reports `origin`, which fixed the biggest one):

- Fallback to the mock is silent: a mistyped `PATHFINDER_ML_DIR` serves 20 careers. A strict mode that raises (and logs on every fallback) is proposed.
- On the mock path 77 of 100 hedge targets are missing from the mock occupations, so `ml.occupation(hedge_soc)` returns `None` and a decision layer would break. v1.2 makes the mock set the demo careers plus their hedge targets (in progress). The demo set stays 20.
- A file with a byte-order mark (what PowerShell's `Out-File` writes) or a non-UTF-8 file raises, even in `status()`. A race in `_load` can make `status()` raise `KeyError`. `occupations()` deep-copies 412 profiles on every call (78 to 110 ms), so the API should cache. `schema_version` is not checked. `status()` returns absolute local paths. None of these are fixed yet **(verify)**.
- **For Avenir's tests:** once real `snapshots/ml/*.json` land, `ML()` prefers them. Pin test fixtures to the mocks, as PR #4 advises: `load_data(ml_dir=<repo>/snapshots/ml/mock, snapshot_dir=tmp)`.

The keyword matcher (`match_tags`): whole-word and alias bugs found by the review: "apprenticeship", "apply" and "apples" matched `computers_coding` through the keyword "app"; "powerful" matched `electricity_energy`; "artificial intelligence" matched `art_drawing`; "I enjoy helping people" matched nothing; `top_k=-1` returned all but the last. **Keyword fix in progress.**

### 7.2 The optional matcher service

File `packages/ml/pathfinder_ml/service.py` (FastAPI, in commit `cb9e169`). Run it with `MATCHER_MODEL=<path or model id> python -m uvicorn pathfinder_ml.service:app --port 8081`.

- `GET /health` returns `{ok, data: {model, device, n_careers, loaded}}`.
- `POST /match` with `{"text", "top_k"}` returns the top careers by embedding similarity (maximum cosine over the career's ESCO text chunks) plus the keyword tags, in the same envelope as the main API. It answers 503 with `error.code = "matcher_unavailable"` when the model is not loaded.
- The backend should call it when `/health` is 200 and otherwise use `ML.match_tags` plus `ML.fit_scores`. That fallback is the pull-the-plug moment for the matcher.
- Tests use a fake embedding model so they run in about a second without downloads. `PATHFINDER_SLOW_TESTS=1` also exercises the real model.
- **Review found:** it has no abstention. Junk or out-of-scope text gets confident-looking matches ("asdf qwerty zxcv" scored 0.399 for Graphic designer; "professional footballer" gave Secondary teacher at 0.409; a real in-scope query scored 0.517). `/health` returns 200 with `n_careers: 0` if `career_texts.json` is missing, so the "use the service if health is 200" rule shows no matches instead of falling back. `top_k` is not validated. **v1.2 (in progress):** abstain below a calibrated score and require loaded careers in `/health`.

### 7.3 The explanation checker `pathfinder_ml.explain` (not committed yet)

Standard library only. It exists in my working copy with tests (`tests/test_explain.py`). Not on any branch yet.

- `template_explanation(occupation)`: deterministic plain-English text from one occupation record. The fallback when the LLM is down, and the reference a draft is checked against.
- `validate_explanation(text, occupation)`: returns a list of problems; empty means the text may be shown. It checks that every number in a draft matches a number in the record (within display rounding) and that every `MUST_MENTION` flag on a metric with a value is mentioned.
- Usage: draft = LLM output; if `validate_explanation` finds nothing, show the draft, else show the template text.
- **Relation to Yehor's adapter (PR #5):** the adapter has its own check (numbers must be in the response, notices copied verbatim, no "you should"). Yehor: tell me whether you want mine as well, or the adapter's check is enough.
- **Review found:** an occupation carries 5 to 7 distinct must-mention flags (median 6), and `employees_only` sits on 4,120 of 5,768 metrics, so forcing every flag into prose produces a wall of caveats. Constant flags should go on the card, not in the text. The template said "most between p25 and p75" for an interquartile range, which is only half of earners; to fix.

### 7.4 Tests

| Suite | What it covers | Count |
| --- | --- | --- |
| `tests/test_api.py` | JSON Schema checks on mock and real files; loader behaviour; flag vocabulary | 28 contract tests in the v1.1 README (19 at the Avenir import) |
| `tests/test_service.py` | Matcher service with a fake model; real model behind `PATHFINDER_SLOW_TESTS=1` | With the above: 38 passed and 1 skipped at `cb9e169` (engineering review) |
| `tests/test_explain.py` | Invented numbers and missing caveats are caught | Uncommitted; count not recorded **(verify)** |

Gaps found by the engineering review:

- The schema accepted all 26 semantic mutations the reviewer tried (wrong unit for a key, exposure 7.5, a hedge pointing at itself, a null group, and so on); it rejected all 10 structural ones.
- Without `jsonschema` installed, 16 of 29 tests in `test_api.py` are skipped and pytest still exits 0. Fail instead of skip in CI.
- No test touches the build scripts; there are no tests for the confidence rules; there is no CI for this package.
- The README test command is bash-only and needs `PYTHONPATH`.
- The reviewer wrote 46 proposed tests; 34 fail on `cb9e169`, exactly the defects listed above. v1.2 adds invariant tests for the confidence rule, history years, resilience centring, reference integrity, the backtest group list and the category map.

---

## 8. (f) What the two reviews found, and the v1.2 fix pass

### 8.1 What the reviews were

Two independent review passes on the committed branch and its artefacts, run by separate Claude Code agents with probe scripts kept outside the repo:

- **Data and statistics review:** pipeline, statistics, claims. Result: **2 blockers**, 13 major, 3 minor, 1 nit. It re-ran my numbers and re-derived many by hand.
- **Engineering review:** loader, artefacts, contract, tests, reproducibility. Result: **no blockers**, 14 major, 6 minor, 1 nit.

### 8.2 What they confirmed was sound

| Area | Confirmed |
| --- | --- |
| ASHE parsing | An independent re-parse of all 19 editions on both sheets (100,268 cells) matches the parquet with 0 mismatches. The sampling-error merge (14,324 cells) also has 0 mismatches. No duplicate year, sheet and code rows |
| Crosswalks | Direction is right: composition weights for pay, split shares for counts. Weights sum to 1; jobs are conserved through the bridge (ratio 0.999) |
| Hand re-derivations | Several published values reproduce (for example software developer pay 38,442 for 2013 against 38,441.7 by hand; COVID resilience 0.0096 against 0.0097). 315 demand trends reproduce to within 5e-5 |
| Hedge similarity | Weighted Jaccard values reproduce exactly (9 of 9 sample pairs) |
| Backtest inputs | Tier inputs use only data up to the base year (no look-ahead). Regression to the mean is ruled out; the minimum-wage explanation holds |
| Contract surface | 412 occupations by 14 metrics; every cited source exists; `value` is null exactly when `suppressed`; `low <= value <= high` everywhere; cross-file integrity holds |
| Reproducibility | With the raw data, all 16 artefacts regenerate byte-identically apart from timestamps; the whole run takes about a minute |
| Hygiene | No secrets in tracked files; `.env` ignored; no licensed financial data in the snapshots |

### 8.3 Findings in plain English and what v1.2 does

Status key: **done** = built in my working copy and not yet pushed; **in progress** = being fixed now; **queued** = on my list, not confirmed started **(verify)**; **team** = needs a decision.

| # | What was wrong | Why it matters | Fix | Status |
| --- | --- | --- | --- | --- |
| 1 | **Blocker.** Pay history and `real_pay_change_10y` are wrong for occupations carved out of old catch-all codes. The confidence rule looked at where the people came from, not whether the old group's median describes them | Cyber security (2135) shows a fake +29% jump in 2021 (38,530 to 49,836) and a +4.6% 10-year change rated medium when the native 2021 to 2025 change is -12%. Other examples: graphic designers (step of -12%), GPs (-47.1%) | Purity and coverage per code. If purity is below 0.5 or coverage below 0.8: low confidence, new flag, 10-year change null or on the native window, and a break in the pay line at 2021. Add ranges | Purity gate **in progress** |
| 2 | **Blocker.** Demand trend rests on the two distorted years and ONS calls the counts indicative | The headline trend moves with the start year | See 5.2 | **In progress** |
| 3 | Confidence and flags do not follow the contract in nine ways | Cards would show more certainty than the data supports | One confidence function and a contract test | **In progress** |
| 4 | Trend confidence ignores tiny, rounded counts | "High" on trends that cannot be told from zero | Derive from propagated sampling error; minimum distinct values and size | **In progress** (with 2) |
| 5 | 2008 shows no signal above ordinary years | A "resilience in 2008" badge would be noise | Off the cards; placebo test published | **Team** (recommended: yes) |
| 6 | Cost of living is tangled with the COVID rebound and unfiltered | Same | Move to 2023 to 2025 with a noise filter, or drop | **Team** |
| 7 | Inflation index timing (April, not tax year) | Typical 10-year real pay change flips sign | Tax-year mean CPIH; rebuild history, 10-year change and baselines; fix the source note | **Done** |
| 8 | Pay and jobs are for experienced adult-rate employees, tax-year based; 2018 and 2025 editions are provisional | Not entry pay | Relabel metrics; add limits; swap in revised editions when I rerun | Relabel **queued**; reruns when editions land |
| 9 | Backtest: survivors only, provisional 2018, tiers are not the picks, overlapping windows, group-list traps | "How our ratings held up" overstates | "How simple rules held up"; add persistence; clean group list | **In progress** |
| 10 | O\*NET agreement is partly circular and partly weak | 82% oversells | Report the no-shared-ESCO figure, sibling baseline and scope (233 of 412) | Wording **queued** |
| 11 | Hedge `evidence` and no "no lower-risk hedge" case; weak and twin links shipped | Misleading hedge panel | Evidence = weaker side; similarity floor; duplicate URIs | **Done**; "none available" case is the decision layer's |
| 12 | Exposure range ignores the ILO's own uncertainty and unscored share | False precision | See 5.4 | **In progress** |
| 13 | Tech slump: wrong category map, not centred, volatile categories | A teacher shows +105% | New SOC 2020 category map | Map **done**; centring, flags, low confidence **in progress** |
| 14 | Bridged job series are partial sums with no coverage tracking (297 of 3,131 bridged full-time job points use under 100% of the share weight; 190 use under 80%) | Some published job lines are nonsense (demo 2452: 11.6, 3.1, 8.9, 2.4, 0.4 ...) | Return coverage; blank points under 0.8; `partial_sources`-style flag; low confidence when coverage varies | **Queued** |
| 15 | ILO and DfE agreement overstated; disagreement flag mostly marks the noise tail | "Independent sources" | Say "two methods"; report within-group agreement | Wording **queued** |
| 16 | README and team-update claims the code does not support (pre-registered, "ratings", "ILO confirmed", "Real" on four weak crises) | Honesty | Reword; add a "what these numbers are not" box | **In progress** (this file already uses the new wording) |
| 17 | Seam test hides per-occupation error; small LFS bases | Bridged pay is less certain than shown | Carry per-occupation seam error into intervals; small-base flag | **Queued** |
| 18 | No tests for pipeline logic; re-running `build_artefacts.py` alone overwrites matcher and eval outputs | Silent regressions | Invariant tests; each stage owns its files | **Queued** |
| 19 | Pay ceiling missing for 377 of 412 | Card row blank | Group fallback (fills about half), flagged; show p75 | **Planned** |
| 20 | Keyword tagger false positives; service has no abstention; `/health` lies with 0 careers | Visible quiz errors | Whole-word matching, fixed keywords, abstain, health check | **In progress** |
| 21 | Mock set missing 77 of 100 hedge targets; silent fallback | Decision layer breaks on mocks | Mock = demo careers plus hedge targets; strict mode | Mock set **in progress**; strict mode **queued** |
| 22 | Contract gaps: undocumented `extra` keys; `eval.bridge_seam` shape changed in v1.1 (not strictly additive); history has gaps for 137 occupations; one-sided ranges | Consumers cannot rely on the docs | Document `extra`; document gaps; test | **Queued** |
| 23 | Loader robustness (BOM, race, deep copy cost, no schema check) | Windows-written files crash it | Fix `utf-8-sig`, lock, cache | **Queued** |
| 24 | ILO licence text and attribution | The sources page shows the licence to judges | "CC BY 4.0 (© ILO 2025), adapted"; add an attribution field; the exposure score is an adaptation and the ILO has not endorsed it **(verify the wording on the live page)** | **Queued** |
| 25 | Cluster notes name internal hosts and paths in `RUNBOOK.md` | Must not go public | Remove before any public release. Avenir PR #2 flagged the same | **Queued**; Avenir's copy needs the same scrub |
| 26 | Reproducibility from a fresh clone: raw data is git-ignored; no fetch manifest, no pinned packages | A teammate cannot rebuild | Fetch script with hashes, pinned requirements, commit the `SOURCE.md` files | **Queued** (after freeze if time is short) |

### 8.4 What v1.2 changes for you

- **Shapes stay compatible with contract v1.1.** No new metric keys are planned, so `vocab.ML_METRICS` is unaffected. Flags are free text in Avenir's models, but new flag names (for example for low purity, indicative counts, fallback to all employees, partial sources) are possible; they will be added to `FLAG_TEXT` and `MUST_MENTION`, and `notices_for` picks them up with no code change.
- **Values will move.** Expect: typical `real_pay_change_10y` near zero or slightly positive instead of -1.2%; demand trends shifting (typical +1.8% a year to about +4.8% a year before centring on the typical occupation); about 500 confidence badges lowered; some pay changes null with a flag; exposure ranges wider; fewer or no 2008 values on cards; tech slump centred; backtest labelled "simple rules". Do not hard-code today's numbers in tests or copy.
- **Mock files grow** beyond 20 occupations (demo careers plus their hedge targets); `demo_set` stays 20.
- `status()` gained `origin`; `mode` is now decided by origin. Additive.

---

## 9. (g) Honest limits

Say these if asked:

- **Employees only.** Pay and job counts come from a survey of employees (ASHE). Freelancers and self-employed people are not counted; freelance-heavy careers (architects, designers) are under-counted. Census is a stretch goal.
- **Not starting pay.** Pay is for adult-rate employees who have held the job for over a year, in the tax year ending 5 April. It excludes apprentices on youth rates.
- **Job counts are indicative.** ONS says so, and 2021 and 2022 were distorted. Trends describe the past; they are not forecasts (past and recent trends correlate at about 0.15).
- **2018 and 2025 are provisional editions;** the revised 2025 edition is due this month.
- **Bridging has error.** Pay lines are bridged across two code changes. The typical error for one occupation is about 4% and can be much larger for occupations carved out of old catch-all codes.
- **Small occupations** get group-level figures more often (marked "estimated").
- **AI exposure is a research estimate** of how many tasks AI could touch, not a prediction that a job disappears, and it cannot be backtested. The two methods agree across broad groups (0.777) much less inside them (0.54 and 0.47).
- **Hedges mean closest skills.** About 7 in 10 occupations have no candidate with clearly lower exposure; 43% of hedges rest on a weaker ISCO fallback. The app must be able to say "no lower-risk hedge available".
- **The track record** shows how simple rules held up over few, overlapping windows. It shows direction, not proof.
- **The tech slump** is measured per job-advert category, not per occupation, and the ONS series ended in Oct 2024.
- **The interest matcher** has only been scored on a small synthetic set where always guessing the same three careers already scores 0.50. Only the team's labels count. Fit scores exist for 20 careers.
- **Reproducibility:** my raw data is git-ignored (about 87 MB), 7 of 10 `SOURCE.md` files have no URL, several file names are hard-coded, some steps are manual (unzipping SOC 2000, saving the ILO page as HTML) and packages are not pinned. With my local data, the rebuild is byte-identical except timestamps.

---

## 10. (h) What I need from the team

| # | Ask | Who | When | My recommendation |
| --- | --- | --- | --- | --- |
| 1 | **Matcher labels:** write about 20 "what I enjoy" texts each, pick the 3 best careers by SOC code ([`packages/ml/eval/LABELLING.md`](../../packages/ml/eval/LABELLING.md) after my push; the file is in KATYATA today). Do not look at the matcher first. Use fictional content, because the files will be committed | 2 or 3 people | 30 minutes, tonight or Sunday early | Needed for the final matcher choice. Without it fit stays "preliminary" |
| 2 | **Confirm the 20 demo careers** (table below) | Whole team | 5 minutes | Confirm as listed |
| 3 | **2008 crisis:** take it off the cards? | Team (Yehor to call it) | Before the cards are built | Yes. It shows nothing beyond an ordinary year. Keep it in "how we checked" as an honest negative result |
| 4 | **Cost-of-living window** | Team | Before freeze | Move to 2023 to 2025, called "recent real pay vs the typical career", with the noise filter; drop if it is still unstable |
| 5 | **Pull the plug,** now that Adzuna is not an ML input | Team (Yehor, Nazar) | Before freeze | Switch off the matcher service and the LLM; the keyword tagger and the template take over, with a badge. Note: `/api/v1/demo/live` currently switches off Adzuna only (PR #5) |
| 6 | **Track-record label** | Team | Before freeze | "How simple rules held up", not "our ratings", with the persistence result |
| 7 | Close stale PR #2, and review and merge this PR; accept my real-artefact push under the 5 MB rule | Yehor | Tonight | n/a |
| 8 | Add the missing sources to `data/manifest.yaml` (section 3.3) | Yehor | Before freeze | Licences are in section 3.1 |
| 9 | Handle "no lower-risk hedge available" in the hedge pick; copy `evidence` from candidate to hedge; handle a null group and `other` in backtest groups | Nazar | When picks are built | n/a |
| 10 | Say whether you want my `validate_explanation` in addition to the adapter's check (7.3) | Yehor | Sunday morning | n/a |
| 11 | Frontend: break job lines at 2021; show "sample data", "estimated", "category level", "sources disagree" badges; give charts a text alternative; name the frontend owner in AGENTS.md | Frontend owner, Yehor | Sunday | n/a |
| 12 | Scrub `packages/ml/RUNBOOK.md` in Avenir (it names internal machines and paths) before the repo goes public | Yehor, me | Before public release | n/a |

The 20 demo careers (same as `eval/LABELLING.md`):

| SOC | Career | SOC | Career |
| --- | --- | --- | --- |
| 2134 | Software developer | 2453 | Quantity surveyor |
| 3544 | Data analyst | 2454 | Chartered surveyor |
| 2133 | IT business analyst or systems designer | 2433 | Actuary, economist or statistician |
| 2135 | Cyber security professional | 2422 | Finance and investment analyst |
| 2141 | Web designer | 2421 | Accountant |
| 2142 | Graphic and multimedia designer | 2254 | Medical radiographer |
| 2451 | Architect | 5241 | Electrician |
| 2452 | Architectural technologist or planner | 2313 | Secondary school teacher |
| 3120 | CAD and architectural technician | 2121 | Civil engineer |
| 3113 | Engineering technician | 2123 | Electrical engineer |

### Plan to the freeze (my own plan; not a promise)

| When | What |
| --- | --- |
| Tonight | Finish v1.2 fixes in section 8.3; job title to occupation lookup for the "first idea" box (built from the ONS coding index; not built yet, and Avenir's catalogue aliases already cover the 20 demo careers); 2015 to 2020 backtest window; rerun the in-house exposure check on the demo careers **(verify)** |
| Sunday 08:00 to 09:30 | Push real artefacts (v1.1 plus matcher plus v1.2) to Avenir as one PR; score the matcher once on the team's labels; freeze the artefacts |
| Sunday 11:30 | Freeze. Anything unfinished goes on the "next" slide: Census self-employed, fine-tuned matcher, more backtest windows |

Cut order from the spec if time runs out: in-house exposure check, fine-tuned matcher, wellbeing rows, fewer than 20 careers.

---

## 11. Decision log (my lines in `docs/decisions.md`, with the reason)

| Date | Decision | Because |
| --- | --- | --- |
| 17 Oct | ILO exposure averaged over all mapped ISCO codes, spread shown, DfE as a UK cross-check, not the dominant code only | One UK occupation spans several ISCO codes whose scores differ by 0.12 on average |
| 17 Oct | Demand trends within each coding era, not one bridged 2011 to 2025 line | Job counts jump more than 25% at the 2021 change for 38% of occupations |
| 17 Oct | "Truthful return": current pay and range plus the real pay path, no projections | High-pay careers grew more slowly in 2013 to 2019 |
| 17 Oct | Bridge the track record to SOC 2020 and flag every bridged value, including in LLM prose | The team wants recent years and crisis behaviour |
| 17 Oct | Add Census 2011 against 2021 counts for self-employed coverage | ASHE misses freelance-heavy careers (not built yet) |
| 17 Oct | Link UK jobs to ESCO by exact title with rules, not by ISCO code alone | 678 shared titles sit under different ISCO codes |
| 17 Oct | Hedges only at the same ONS skill level | Otherwise hedges were step-downs (civil engineer to construction trades) |
| 17 Oct | Crisis job counts at occupation level only with at least 50,000 jobs (else the 3-digit group) | Small occupations gave artefacts (radiographers -16% in COVID) |
| 17 Oct | 2008 resilience as the worse of jobs and real pay over April 2008 to 2009 | Employee counts missed the crash (architects up by 2010). **The review shows this definition fails a placebo test; see 5.3** |
| 17 Oct | Tech slump from ONS job-advert categories, flagged category level | Adverts are the only free source covering 2022 to 2024 |
| 17 Oct | Gemini (free tier, public or synthetic text only) plus a local model, over waiting for ELM; Adzuna dropped | ELM key needs approval; Adzuna is paid |
| 18 Oct | Ship the base embedding model for the matcher, not the fine-tune | Fine-tune gained +0.03 hit@3 (interval touching zero) and lost at hit@1 |
| 18 Oct | Train the matcher on the laptop GPU, not the cluster | A 110M-parameter model fine-tunes in 2 minutes locally, and the demo must not depend on cluster access |

---

## 12. Reproduce (needs my local raw data)

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
```

Matcher steps (training statements need a Gemini key in `.env`, which is never committed): `m1_gen_statements.py`, `m1_train.py`, `m1_matcher.py eval ...`, `m1_matcher.py build-fit ...`. When the team's labels exist: `m1_matcher.py eval ... --split test` **once**, then `build-fit` with the winning method.

Python packages used: pandas, numpy, scipy, pyarrow, openpyxl, xlrd, jsonschema (tests), sentence-transformers and torch (matcher only), fastapi and httpx (service and its tests). The scripts need Python 3.10 or later.

## 13. Glossary

| Term | Meaning |
| --- | --- |
| ASHE | Annual Survey of Hours and Earnings (ONS): pay and jobs by occupation, employees only |
| SOC 2000, 2010, 2020 | The UK Standard Occupational Classification in three versions. The app uses SOC 2020 |
| ISCO-08 | The international occupation classification the ILO and ESCO use |
| CPIH | ONS consumer price index including housing costs; used to take inflation out of pay |
| CV | Coefficient of variation: ONS's measure of sampling error for an estimate |
| ESCO | European occupation and skills classification |
| Theil-Sen | A trend line that ignores outliers; gives an interval |
| BM25 | A classic keyword-search score |
| BGE | The sentence-embedding model used for the matcher |
| Cosine similarity | How close two embeddings are (1 is identical) |
| Weighted Jaccard | Overlap of two weighted skill lists: shared weight divided by combined weight |
| hit@3 | Share of test texts where one of the labelled careers is in the matcher's top 3 |
| MRR | Mean reciprocal rank: how high the first correct career sits, on average |
| Placebo test | Running the same measure in ordinary years to see whether the crisis year really stands out |
| Purity | Share of an old code's people who land in the new code. Low purity means the old code's median does not describe the new one |
