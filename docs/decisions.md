# Decisions

One line per decision, newest at the bottom. Agents: read this before undoing anything.

- <time> <who>: Chose <X> over <Y> because <Z>.
- 17 Oct Yehor: PRs required on `main`, squash merge only, because it keeps history to one readable commit per change.
- 17 Oct Arsenii (ML): Chose ILO exposure averaged over all mapped ISCO codes, with the spread shown and a DfE UK cross-check, over the dominant code only, because one UK occupation spans several ISCO codes whose scores differ by 0.12 on average.
- 17 Oct Arsenii (ML): Chose demand trends within each coding era (2011-19, 2021-25) over one bridged 2011-25 line, because job counts jump more than 25% at the 2021 code change for 38% of occupations.
- 17 Oct Arsenii (ML): Chose "truthful return" (current pay level and range plus the real pay path, no projections) over projected pay growth, because high-pay careers grew more slowly in 2013-19 and projections would mislead.
- 17 Oct Arsenii (ML): Chose to bridge the track record to SOC 2020 and flag every bridged value downstream, including in LLM prose, over keeping it in the SOC 2010 era only, because the team wants recent years and crisis behaviour (COVID, cost of living, tech slump, 2008).
- 17 Oct Arsenii (ML): Chose to add Census 2011 vs 2021 occupation counts for self-employed coverage over an "employees only" label alone, because ASHE misses freelance-heavy careers.

- 17 Oct Codex for Illia: Combine fetched Avenir branch tips locally on codex/complete-career-experience. Max’s complete prototype is the experience baseline; import Arsenii’s exact latest cb9e169 ML slice with provenance, keep historical need distinct from forecasts, and build the user’s five-match/rank-three flow in apps/web. Apple HIG guides a neutral/green interface. No review workflow or publication requested.

- 17 Oct Codex for Illia: Replace the public entry with Aventier mission → reassurance → two starting points. Known-direction and exploring conversations now return three options using the supplied ML tags/affinities; known careers remain labelled references, and guided chat is not presented as a live LLM. Preserve desktop top navigation and pathway tools.
