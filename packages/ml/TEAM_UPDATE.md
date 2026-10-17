# ML update for the team (contract v1.1)

Arsenii, night of 17-18 Oct 2026. About 5 minutes to read. Follows the v1.0 contract and mocks in PR #9; what changed is in section 4.

## 1. TL;DR

- **Real data is in.** `snapshots/ml/` now holds real (preliminary) evidence for all **412 UK occupations**: pay, real pay since 2007, demand, AI exposure, resilience in four crises, hedge careers and the track record. The 20 demo careers are also in `snapshots/ml/mock/`.
- **Your code shouldn't change.** The shapes are the v1.0 ones plus additions only. `ML()` now reads the real files automatically.
- **The interest-to-career fit is now real too** (embedding-based affinities, plus an optional matcher service), but its final sign-off needs your labels (section 7): it has only been scored on a synthetic development set so far.

## 2. The whole project in one picture

**Pathfinder** treats a career like an investment. Amira (17, S6, Glasgow) answers a short quiz and names the career she first had in mind. She gets three picks (Ambitious, Balanced, Safe), each compared with her first idea, plus a hedge career, a track record and a roadmap.

```
 Quiz (interests, quals, slider)            [Frontend]
        |
 API: profile, recommendations, careers,    [Backend, OpenAPI]
      hedge, backtest, routes, sources
        |
 Decision layer: fit gate, picks,           [Decision logic: visible rules, no LLM]
 hedge choice, comparison, roadmap rules
        |
 Evidence (snapshots/ml, Python ML())       [ML: Arsenii]
 Catalogue, routes, wellbeing               [Data/ETL]
 Plain-English explanation + fallback       [AI/glue: LLM writes prose, code supplies numbers]
```

| Card row | Investment idea | Comes from |
| --- | --- | --- |
| Fit | Suitability | ML `fit.json` (+ the decision layer's eligibility gate) |
| Pay now, range, ceiling; real pay path | Expected return | ML `occupations.json`, `history.json` |
| Demand trend; crisis resilience | Market risk | ML |
| Automation exposure | Disruption risk | ML |
| Confidence badges and caveats | Forecast uncertainty | ML (every number) |
| Hedge career | Diversification | ML candidates, decision layer picks |
| "Pick a past year" | Track record | ML `backtest.json` |
| Routes, entry requirements, wellbeing | Due diligence | Data/ETL |

## 3. What kind of AI is this? (RAG? search? cosine? clustering?)

**Mostly an evidence engine:** careful statistics over official datasets, a few small, checkable models, and visible rules. Not a chatbot. Where each technique sits:

| Technique | Used? | Where and why |
| --- | --- | --- |
| Statistics and econometrics | **Yes, the core** | Robust trends (Theil-Sen) with intervals, bootstrap confidence intervals, inflation adjustment, bridging old occupation codes to new ones, rank correlation between sources, an out-of-sample backtest. This is where the numbers come from |
| Information retrieval / search | **Yes** | (1) Matching free text ("I like drawing and fixing bikes") to careers is a retrieval problem: keyword search now, embeddings next. (2) Linking 32,000 UK job titles to 3,000 ESCO occupations is exact-match search under rules |
| Cosine similarity | **Yes, in the matcher's next step** | Off-the-shelf sentence embeddings (BGE-base, MIT licence) of career descriptions vs the user's text. Kept only if it beats keyword search on our human test set |
| Set similarity (weighted Jaccard, IDF weighting) | **Yes** | Hedge careers: occupations sharing the most *distinctive* ESCO skills. Rare skills count more, like TF-IDF in search engines |
| Model training | **One optional model** | A contrastive fine-tune of the matcher on human-reviewed pairs, only if it beats the simpler versions. Everything else is computed, not trained: small data, explainability, and no overfitting |
| LLMs | **As tools, not deciders** | Offline: drafting candidate interest phrases (reviewed by people) and a task-level exposure check. Online: writing the explanation from numbers our API returns, with a template fallback. Gemini free tier on public or synthetic text only; a local model on our GPU cluster for bulk jobs |
| RAG with a vector store | **No** | The LLM gets the structured numbers straight from our API (a lookup, not a vector search) and may only cite those numbers. Simpler, and it can't make up a salary |
| Clustering | **No** | Nothing in the decision needs it |

Pitch line: *"Every number is sourced and computed; models only rank or match, and each is beaten-or-dropped against a simpler baseline; the LLM only explains."*

## 4. What changed since the v1.0 contract (PR #9)

Additions only, so v1.0 code keeps working. Full table at the top of [`CONTRACTS.md`](CONTRACTS.md).

| Change | What it means for you |
| --- | --- |
| Real artefacts for all 412 occupations in `snapshots/ml/` | `ML()` picks them up; the mocks stay as the fallback and test fixtures |
| New metric `young_worker_share` (2016, includes self-employed) | Optional card line: "in 2016, 9% of people in this job were under 25" |
| New flags `category_level`, `bridged_soc2000`, `sources_disagree` | All must be mentioned by the LLM; `FLAG_TEXT` has the sentences |
| `exposure_uk` filled (DfE as a percentile) | A cross-check; don't show it as a second headline |
| Tech slump and 2008 crisis are real | Show `extra.adverts_category` for the tech slump; 2008 `extra` has the jobs and pay parts |
| Hedge items have `evidence` | Show "estimate" when it says so |
| History starts in 2007 (pay only before 2011) | Job lines start in 2011 and break at 2021 |

## 5. My part in detail

| Package | What the user sees | How (model / method) | Data | Why this way | Where in the app | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Data pipeline | Every number, with source and year | Parsers plus code bridging across three occupation coding systems | ONS ASHE 2007-2025, ONS crosswalks, coding index, CPIH | Official, free, UK-wide; bridging tested at both code changes | All cards | Done |
| Expected return | Pay now and range; real pay path since 2007 | Medians and percentiles; inflation-adjusted series; no projections | ASHE, CPIH | "Truthful": real pay fell for most careers since 2011, and we show that | Card, chart | Real |
| Demand | Is the job growing? | Robust trend with a 90% interval, within one coding era | ASHE | Job counts break at code changes, so trends never cross them | Card | Real |
| Crisis resilience | How it held up in COVID, the cost-of-living shock, the tech slump and 2008 | Change in the crisis window vs the typical occupation; group figures for small jobs | ASHE, ONS job adverts (Adzuna) | The team's priority: which careers survive shocks | Card badges | Real |
| Automation exposure | Exposure score with a range | ILO 2025 averaged across mapped codes; DfE cross-check | ILO WP140, DfE 2023 | Two independent sources; disagreement shown, not hidden | Card | Real |
| Hedge career | "A related job with the same skills, lower risk" | ESCO skill overlap (weighted Jaccard), same skill level | ESCO, ONS coding index; O*NET as a check | Explainable (lists the shared skills); 82% agreement with O*NET vs 28% random | Hedge panel | Real |
| Fit | How well a career matches her interests | BM25 → embeddings (cosine) → fine-tune, each kept only if better. Shipped: base-model embeddings (the fine-tune gained only +0.03 on dev, so it stays on the bench) | ESCO text; 400 synthetic training statements; human labels for the test | Avoids overfitting; stdlib tag chain at runtime, optional embedding service when up | Quiz → picks; `POST /match` | **Real (preliminary); final score needs your labels** |
| Track record | "Pick a past year": how our ratings held up | Fixed tier rules, outcomes 5 years later, intervals | ASHE | No careers tool does this; an honest result even when it's modest | Track-record view | Real (3 windows) |
| Quality layer | Confidence badges, caveats, sources page, "how we checked" | Flags, confidence rules, evaluation file | All of the above | Trust: engineers judge the failure modes | Everywhere | Real |

## 6. Execution plan (to Sunday midday)

| When | What |
| --- | --- |
| Done tonight | Data pipeline; hedges and their O*NET check; exposure cross-check; crisis measures; real artefacts v1.1; 28 contract tests |
| Done overnight | Matcher: BM25, embeddings and a local fine-tune compared on a synthetic dev set (chance 0.36; BM25 0.70; embeddings 0.90; fine-tune 0.93, not a clear gain, not shipped). Real `fit.json` from embedding affinities. Optional matcher service with tests. Everything ran on the laptop; no cluster needed |
| Sunday 08:00-09:30 | Score the matcher **once** on your test labels; ship the fine-tune only if it wins there; freeze the artefacts; help integration; write the "how we checked" text |
| Sunday 11:30 | Feature freeze. Anything unfinished goes on the "next" slide: Census self-employed, fine-tuned matcher, more backtest windows |

## 7. What I need from you

| Ask | Who | Time |
| --- | --- | --- |
| **Matcher labels:** write about 20 "what I enjoy" texts each and pick 3 careers ([`eval/LABELLING.md`](eval/LABELLING.md)). Don't look at the matcher first | 2-3 people | 30 minutes |
| Confirm the 20 demo careers (list in `eval/LABELLING.md`) | Whole team | 5 minutes |
| Merge PR #9 and the v1.1 PR; adopt `CONTRACTS.md` into `docs/contracts.md` | Yehor | |
| Confirm the split: ML owns pay, demand, exposure and resilience; ETL owns the catalogue, routes, wellbeing and stress | Yehor + ETL owner | |
| Backend: load with `ML()`; return metric flags in the API response; for free-text interests call the matcher service (`POST /match`) when its `/health` is 200, else `ML.match_tags` + `ML.fit_scores` | Backend owner | |
| Frontend: break job lines at 2021; show "sample data", "estimated", "category level" and "sources disagree" badges; give the timeline a text alternative | Frontend owner | |
| LLM explanations: cite only API numbers, mention every `MUST_MENTION` flag, template fallback; free-tier Gemini only with public or synthetic text | AI/glue owner | |

## 8. Honest limits (say these if asked)

- **Employees only** for pay and jobs (ASHE). Freelance-heavy careers are under-counted; Census figures with self-employed are a stretch goal.
- **AI exposure is a research estimate** of task exposure, not a prediction that a job disappears. It can't be backtested, because no historical index exists.
- **Small occupations** get group-level figures more often (marked "estimated").
- **The track record** uses few, overlapping windows. It shows direction, not proof.
- **The tech slump** is measured per job-advert category, not per occupation.
