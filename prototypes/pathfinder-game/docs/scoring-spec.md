# Scoring specification (for external review)

This file describes everything that decides a ranking. The code that implements it is `backend/app/scoring.py`. No model or AI call takes part in ranking.

## 1. Inputs per occupation (SOC 2020)

| Signal | Raw input | Source |
| --- | --- | --- |
| Interest fit | O*NET RIASEC profile (1–7) | O*NET, crosswalked to SOC 2020 |
| Demand by 2035 | Projected % employment change 2025–2035, floored at 0, × regional multiplier | Skills England 2026 |
| Demand now | Skill-shortage vacancy density %, × regional multiplier, capped at 100 | Employer Skills Survey 2024 |
| Pay | Median full-time annual gross pay | ASHE |
| AI resilience | 1 − mean task-level generative-AI exposure | ILO WP140 (2025) |
| Head start | 0.6 × min(1, matched subjects / min(2, listed)) + 0.4 × min(1, matched experience / min(2, listed)) | Curated mapping |

The regional multiplier is set per sector and region (`regions.json`). The UK-wide multiplier is 1.

## 2. Scaling

Each market input is min-max scaled across all occupations under the current region, then clipped to [0, 1]. Interest fit is the Pearson correlation between the user's six RIASEC means and the occupation's profile, floored at 0.

## 3. Score

`score = 100 × Σ wᵢ · sᵢ / Σ wⱼ`, where the sums run only over signals that have data. Default weights:

| Signal | Interest | Demand 2035 | Demand now | Pay | AI resilience | Head start |
| --- | --- | --- | --- | --- | --- | --- |
| Weight | 0.30 | 0.20 | 0.15 | 0.15 | 0.10 | 0.10 |

The user can change the weights. They are renormalised to sum to 1.

## 4. Safeguards

- **Interest gate:** interest fit < 0.5 means the career is never shown, whatever the weights.
- **Missing data:** a missing signal is excluded and the remaining weights are renormalised. Nothing is imputed.
- **Flat profile:** if all six RIASEC means are equal, no results are shown.
- **Ties:** a deterministic tie-break on score, then fit, then title.

## 5. Per-pick analysis (three picks)

### Stress test

Each scenario is re-scored against the baseline scaling bounds, so scores stay comparable.

| Scenario | Change applied |
| --- | --- |
| AI moves faster | exposure × 1.5 for every job, capped at 1 |
| Your sector slows | growth −8 pts and shortages −15 pts across the pick's sector |
| Pay falls behind | pay × 0.9 across the pick's sector |
| Your interests shift | the pick's fit −0.15 |

A pick "holds" a scenario if it stays in the user's top 5 among eligible careers.

### Hedge career

The hedge is chosen from eligible careers that are not already picks and that either sit in a different sector or have AI exposure at least 0.08 lower.

- **Candidates are ordered by:** (different sector, similarity, score).
- **Similarity:** 0.5 × max(0, Pearson(profile_a, profile_b)) + 0.5 × Jaccard(subjects ∪ experience).

### Confidence

Confidence starts at 1.0 and loses points for weaknesses in the evidence:

| Condition | Change |
| --- | --- |
| Each missing market signal | −0.15 |
| ONS pay quality "use with caution" | −0.10 |
| SOC 2010→2020 split | −0.10 |
| SOC 2010→2020 new code | −0.20 |
| Fit < 0.6 | −0.10 |
| Holds 2 or fewer of the 4 stress tests | −0.15 |

The result maps to a level: **High** at 0.75 or above, **Medium** at 0.5 or above, otherwise **Low**.

## 6. Self-grade (backtest)

`backend/app/backtest.py`. For each year Y in 2011–2019, the demand signal is rebuilt from that year's inputs only: shortage density and the projection published then. It is compared with employment change from Y to Y+4.

**Metrics:**
- Spearman rank correlation.
- Top-third hit rate against the median, where chance is 50%.
- Mean change in the top third against the bottom third.

**Robustness check:** the "exclude bridged codes" view drops split and new SOC codes.

**Status:** the current series is SYNTHETIC (see `scripts/build_demo_snapshots.py`) until the real ESS, Working Futures, LFS and ASHE series are loaded.

## Questions for the reviewer

1. Are the default weights defensible for a 16-year-old's first shortlist?
2. Is floored Pearson correlation the right measure for interest fit, compared with, say, Euclidean distance on top-three codes?
3. Should pay be scaled on its log, to reduce the pull of high-pay outliers?
4. Is a 4-year horizon long enough for the backtest, given study takes 2 to 6 years?
