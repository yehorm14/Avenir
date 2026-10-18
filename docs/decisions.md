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

- 17 Oct Codex for Illia: QuantSoc is the chosen visual reference, replacing the earlier Apple/green direction. Use its researched Inter, charcoal/silver palette, floating pill navigation, navy hero, original gold signal paths, outlined panels and blue chart/selection accents throughout Aventier. Preserve all discovery and evidence behavior; desktop is the priority.

- 17 Oct Codex for Illia: Simplify the public entry to one screen. Remove the top-left logo, header/hero/footer slogans and reassurance screen; place the known-career and discovery choices directly under the mission with two-word action labels.

- 17 Oct Codex for Illia: Keep Home, Quiz, Jobs and Chatbot in the primary menu on every screen. Remove the profile/privacy menu and location questions. Jobs browses the supplied career catalogue and Chatbot works before quiz completion; selected-career workspace tools remain available.

- 18 Oct Codex for Illia: Jobs prioritizes electricians and plumbers using MAC 2026 evidence, with exact Skills England 2025 demand categories kept separate. Add canonical plumber5315 to the catalogue only; matching remains calibrated to20 roles. Show sourced employment/pay history and published sector outlook horizons; two-year salary is an editable scenario with explicit assumptions, not an asserted forecast.

- 18 Oct Codex launch integration: Ship the full412-profile evidence directory with20-role interest matching, a durable browser-local decision/action plan and a single key-free production service. Exclude synthetic catalogue inputs from canonical ranking and lower confidence for missing inputs; preserve real ML observations, source years, missing-year gaps and wider-group/England labels. Keep school/pilot/funding figures as explicit hypotheses.
- 18 Oct Codex release: Create codex/hackathon-release at the user's request, preserve the completed launch branch, make every documented app startup serve both API layers, and verify fresh setup before handoff. Pin Vite 6.4.4 on its supported security line to close inherited audit findings without changing React or the design.
- 18 Oct Codex demo polish: Focus the desktop demo on Computer Science and Finance, using explicit supported occupations and direct evidence dashboards; preserve existing ML/API values and discovery, keep starting-pay guides distinct from workforce medians, and allow direct plans without fabricating completed matching.

- 18 Oct Codex final delivery: Integrate Arsenii’s exact MLv1.2 release atomically with metadata-aware UI/API labels, purity gaps and exact fixture regeneration; exclude failed-placebo crisis inputs at the production boundary while preserving raw evidence. Add a transparent subject-scoped priority comparison and a checksummed prebuilt submission, keeping the timed demo to CS/Finance and human-controlled next actions.

- 18 Oct, team (Yehor): the primary demo is Amira with first idea architect (AGENTS.md section 1); CS/Finance stays a secondary journey.
- 18 Oct Codex plan cleanup: Apply the user's 21 annotations to My plan with a compact monthly dropdown and prepared career chat; preserve stored notes/routes and the numeric comparison while keeping detailed evidence on its separate view.
- 18 Oct Codex final navigation: On final-delivery, use the user's exact Home, Quiz, Jobs, My plan and Chatbot menu; retain the current design and Home dashboard entry points, preserve guide URLs, and publish only this branch.
- 18 Oct Codex single-page plan: At the user's request, remove the overview's inner tabs and repeated comparison tables; keep one career/chat/action view with direct Change career and View pathway links, preserving saved data and detailed workspace routes.
- 18 Oct Codex main sync: Merge origin/main eaf0740 into codex/final-delivery, retaining the requested five-item menu, simplified My plan and removed quiz copy while bringing in the Amira Home, updated Jobs evidence, grounded Chatbot and BlackRock card.
- 18 Oct Codex Matches cleanup: Remove the redundant Matches page eyebrow, intro, list labels, repeated source caveats and priority disclaimer, plus the top-left Aventier mark/name; keep career cards, priority controls, selected-career tools and secondary workspace navigation.
- 18 Oct Codex Chatbot cleanup: Use generic Chatbot/Career chatbot copy and remove the standalone prepared-guide badge, voice playback, footer note and composer hint; keep career selection as the evidence context for answers.
- 18 Oct Codex plan/jobs cleanup: Remove the entire selected My plan “Explore first / Change career” status row per annotation; make the full Jobs Sources/Attributions content a native, closed-by-default disclosure so it remains accessible without occupying the page.
