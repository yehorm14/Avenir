# Arsenii's ML contract — context for Aventir

Inspected 17 October 2026 after fetching origin. Branch: `origin/arsenii/ml-data`, tip `662f15c` (context/PR reference); latest implementation commit `fccee2d`. The branch references PR #9. This is a read-only assessment, not a merge or a change to the shared contract.

Primary references on that branch:

- [ML contract](https://github.com/yehorm14/KATYATA/blob/662f15c/packages/ml/CONTRACTS.md)
- [Slice status and methods](https://github.com/yehorm14/KATYATA/blob/662f15c/packages/ml/README.md)
- [Provenance registry](https://github.com/yehorm14/KATYATA/blob/662f15c/snapshots/ml/mock/sources.json)
- [Python loader](https://github.com/yehorm14/KATYATA/blob/662f15c/packages/ml/pathfinder_ml/api.py)

## Available in the committed artefacts

The `mock` folder contains both preliminary real data and placeholders. Read each file and metric's `status`; the folder name alone does not establish whether a value is real.

| Evidence | Source | Current scope / status | Useful display |
| --- | --- | --- | --- |
| Annual pay distribution and employee jobs | ONS ASHE Table 14 | Preliminary real metrics for 20 demo SOC occupation groups | Median pay, p25–p75 band, p10/p90 where available |
| Pay and jobs history | ASHE, SOC crosswalks and CPIH | 2011–2025, 15 annual observations for each of the 20 groups | Nominal/real pay; employee job counts with a coding break |
| Inflation adjustment | ONS CPIH | Loaded; April 2025 price base | Real pay history and ten-year change |
| Occupation mapping | ONS SOC 2010/2020 crosswalk and SOC 2020 coding index | Loaded in Arsenii's pipeline; SOC-to-ISCO shares included in occupation artefacts | Join and explain code-era changes |
| GenAI task exposure | ILO WP140 (2025) | Preliminary research estimates weighted across mapped ISCO codes | Exposure score with its spread; not a job-loss probability |
| Crisis resilience | ASHE + CPIH | COVID and cost-of-living measures preliminary | Historical comparison with the typical occupation |
| Historical track record | Derived backtests | 2013→2018, 2014→2019 and 2019→2024; latest window pay-only | Historical outcomes with caveats, not future performance claims |

The committed `occupations.json` contains 20 records and 260 metric objects: 200 marked preliminary, 60 pending. Coverage is not yet all 412 SOC 2020 occupation groups. Arsenii reports the broader ASHE, coding-index, CPIH and ILO inputs loaded locally; raw inputs are not in Git.

## Still mock or pending

- **Interest fit:** 16 checklist tags and a working deterministic keyword matcher; affinities/fit scores are hand-assigned placeholders. Embeddings and fine-tuning are planned and must beat a held-out baseline before shipping.
- **Alternative careers / hedges:** placeholder candidates and similarity scores; real ESCO skill-overlap candidates are pending. Do not present the existing scores as learned similarity.
- **Pending sources:** DfE UK exposure cross-check, online job-advert history, older ASHE for the 2008 crisis and Census coverage of the self-employed. ESCO v1.2.1 CSV is pending for Arsenii's pipeline; Aventir separately has a complete ESCO API import, with its API version undeclared and five missing skill profiles. These are not automatically interchangeable snapshots.
- **Live Adzuna, official education/apprenticeship feeds, friendly descriptions and entry requirements:** owned outside the ML slice. This commit does not deliver them. No social/reels feed is supplied.
- **No trained model is shipped.** The proposed in-house task labelling validates the published exposure index; it does not supply a second public risk number.

## What the LLM can provide

The LLM belongs to the backend/AI glue layer. Arsenii supplies evidence and caveat vocabulary, not a ready hosted conversational model or endpoint.

The LLM can explain a career's evidence in plain language, answer questions using those facts, explain rule-selected career comparisons and alternatives, and suggest small activities or follow-up questions to explore interests. Once verified route data exists, it can explain the supplied route options and roadmap. It should not invent course eligibility, vacancies or costs.

It cannot supply missing statistics, future pay projections, a probability of job loss, or a claim of guaranteed safety. It does not choose the Ambitious/Balanced/Safe picks: the separate decision layer owns those visible rules. Free-text interest extraction through an LLM is AI/glue work; the current ML implementation is a keyword baseline.

Every numerical explanation must preserve source, period, confidence and granularity, and carry the relevant `MUST_MENTION` caveats: older-code estimates, the 2021 coding change, COVID distortions, employee-only coverage, parent-group estimates and sample data. The frontend must preserve pending/null values and preliminary/mock labels.

## Implications for our next sprint

1. Add a reviewed mapping between Aventir's ESCO occupation IDs and Arsenii's UK `soc2020` groups. Their identities and granularity differ; don't join by title or assume ESCO's code is SOC 2020.
2. Consume `pathfinder_ml.ML` inside FastAPI, or its JSON directly. Preserve per-file fallback and per-metric status. Replacing mock files with real artefacts should not require frontend changes.
3. For mapped demo careers, use occupation pay history and employee job counts as the primary career charts. Keep ONS industry vacancies separately labelled as broader context. Employment counts are not open vacancies.
4. Keep NCS starter/experienced guidance separate from ASHE pay percentiles. Neither p10 nor p25 is an entry-level salary, and p90 is not a guaranteed ceiling.
5. Break employee job-count lines at 2021. Distinguish bridged pre-2021 estimates and flag 2020. Current historical tiers cannot backtest AI exposure.
6. Pass structured metrics and required caveats to the LLM; validate explanations against those facts. Keep unavailable fit/hedge models labelled sample or hidden until real artefacts land.

`docs/contracts.md` remains a template on the inspected branch. `packages/ml/CONTRACTS.md` is a proposal for Yehor to adopt, including moving pay/demand ownership into ML while ETL retains the display catalogue and routes.

The exported branch was tested without switching or editing our workspace: 11 loader/behaviour tests passed; 8 JSON Schema checks were skipped because the current Python environment lacks `jsonschema`. Those schema checks have not been independently verified here.

The current Aventir app remains unchanged by this inspection and has not yet been connected to these ML artefacts.
