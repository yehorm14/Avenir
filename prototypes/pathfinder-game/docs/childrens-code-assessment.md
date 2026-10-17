# Children's Code assessment (draft)

Pathfinder is used by people aged 15 to 18, so the ICO Age Appropriate Design Code (the Children's Code) applies. This is a working assessment against its 15 standards. It is a draft for a data-protection review, not a signed-off DPIA.

**What we process:**
- Quiz answers (60 numbers from 1 to 5).
- Chosen subjects and experience.
- Region.
- Optional free-text descriptions (discovery).
- Optional questions typed into "Ask about this result".

**Where it goes:**
- Everything is sent to our scoring API for one request, and nothing is written to disk or a database.
- Answers, choices and the watchlist are kept in the browser's `localStorage` on the user's device.
- There are no accounts, no analytics, and no third-party scripts. Fonts are bundled.

| # | Standard | How Pathfinder meets it | Gaps / to do |
| --- | --- | --- | --- |
| 1 | Best interests of the child | The purpose is to help a young person choose what to explore. No ads, no monetisation of data. Interest fit gates every result, so we never push a pupil towards demand alone. | External review of the scoring by a careers professional (planned). |
| 2 | Data protection impact assessment | This document is the starting point. | Complete a full DPIA before any school pilot. |
| 3 | Age-appropriate application | Everyone is treated as a child: one high-privacy mode, with no age gate needed. | — |
| 4 | Transparency | Plain-English footer and Trust page say what is processed and where. Every figure links to its source. | Short privacy notice written for 16-year-olds and tested with pupils. |
| 5 | Detrimental use of data | No engagement loops. The watchlist is opt-in and capped at 5. | — |
| 6 | Policies and community standards | No user-generated content is published. | — |
| 7 | Default settings | Nothing leaves the device beyond the scoring request. Email alerts (from the plan) stay off unless the user opts in with consent. | Email alerts are not built. If added, require explicit opt-in and parental-consent rules for under-13s (out of scope: users are 15+). |
| 8 | Data minimisation | No name, email, school, date of birth or location beyond a region chosen from a list. | — |
| 9 | Data sharing | None. The optional LLM is self-hosted (own GPUs) and receives only the question and our evidence lines, not quiz answers. | If an external LLM API is ever used, contract terms must forbid retention and training. |
| 10 | Geolocation | Not used. The region is picked by the user. | — |
| 11 | Parental controls | Not applicable: no monitoring features. | — |
| 12 | Profiling | The interest profile **is** the service the user asks for. It is computed per request, shown to the user, and never stored server-side. AI does not rank. | Keep profiling scoped to the request; add a line on the Trust page explaining it. |
| 13 | Nudge techniques | The app is game-styled (character, party, quests, XP, arcade), so this standard matters most here. **Rules we hold to:** no streaks, no daily rewards, no countdowns, no loot or random rewards, no pupil leaderboards, and no social comparison. XP is awarded only for real-world evidence the pupil ticks, never for time spent or taps. The arcade shows no points for playing, and says plainly when the algorithm wins. Stress tests and backups show downside as plainly as upside. | Review the game wording with pupils and a safeguarding lead. Keep any future share card free of personal data. |
| 14 | Connected toys and devices | Not applicable. | — |
| 15 | Online tools | "Clear my data on this device" button on the Trust page wipes all local storage. | — |

## Server logs

Uvicorn access logs record request paths, not bodies. In production, turn off access logging or keep it for at most 7 days. Free text is never logged.

## Radar and opportunities

- **No tracking.** The radar stores nothing on a server. Your chosen fields, stage, the opportunities you tick, and the list of ones you've already seen are kept in the browser only, and wiped by "Clear my data".
- **No daily push or email.** We do not message anyone. A future opt-in digest needs explicit consent and its own assessment before it is built.
- **No ads or paid placement.** Entries are included on relevance and eligibility, never on payment. Links go to the organiser's own site, and we say that dates and eligibility must be checked there.
- **External links.** Pupils leave the app to organisers' sites, which we do not control. Copy must make clear that nothing on those sites is endorsed by us, and a safeguarding lead should review the list before launch.
- **Nothing sent to organisers.** We do not pass a pupil's details to any organiser.

## Game design rules

These rules apply to every game feature, and any new one must meet them:

1. **Evidence, not engagement.** XP and levels come only from ticked real-world evidence (a certificate, a visit, a project).
2. **No pressure.** No streaks, timers, daily bonuses or "come back" messages. A pupil can leave for a month and lose nothing.
3. **No wrong career.** A class is a label for interests today. Respec is always one tap away, and the serious analysis is always one tap away.
4. **Honest losses.** The arcade tells pupils when the algorithm beat them, and why a small sample is noisy.
5. **Private by default.** Progress, classes and ticks stay in the browser. There is no sharing or comparison between pupils.
