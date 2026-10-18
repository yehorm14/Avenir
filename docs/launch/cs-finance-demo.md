# Computer Science and Finance demo

> **Secondary journey.** The primary demo is Amira with first idea architect: see [demo-script.md](demo-script.md). This CS/Finance path stays available from Home.

This secondary journey follows **Amira, 17, in Glasgow, good at maths and choosing between Computer Science and Finance**. Her decision is which role to explore first and what practical step to take this month. Use this page for rehearsal and claim checks; the timed demo is [Amira and architect](demo-script.md).

## Start the final release

From the repository root, with Node 20+ and Python 3.12+:

```sh
bash scripts/setup.sh
node scripts/run-app.mjs --production
```

Open [Avenier](http://127.0.0.1:4175). `AVENIR_PORT` can select a different free production port. The complete UI and both API layers run from one origin without API keys. Use [check-setup and the release gate](README.md#run-and-verify) before the presentation. The earlier 4186 preview and older branch notes describe the previous polish checkpoint, not the final integrated release.

## Primary journey

1. **Choose a subject.** Home opens Computer Science or Finance directly. CS covers Software developer, Data analyst, IT business analyst/systems designer and Cyber security professional. Finance covers Finance/investment analyst, Accountant and the combined Actuary/economist/statistician occupation group.
2. **Read Evidence.** Switch occupations and inspect source periods, pay distributions, employment counts, task exposure and histories. Distinguish ONS workforce medians from the NCS example-role Starting pay guide. Course and learning links are examples; save a relevant organiser if useful.
3. **Compare priorities.** Open Compare and move the Pay / Employment trend slider. Presets make the trade-off easy to show. Read the current recommendation, why it leads on these weights and what is given up. Results stay within the selected subject, and no interest profile is inferred. Missing inputs, comparison coverage and ties must remain visible.
4. **Choose a role.** Amira decides whether to use the suggested role or inspect another. Build my plan opens the selected role's pathway without marking the broader quiz complete or adding unrelated comparison careers.
5. **Choose a route and next action.** Compare University and Earn & learn, then open My plan, add a personal reason and choose a practical task. Save or download the plan; refresh and confirm the route, note, checked actions and saved links persist.
6. **Inspect checks or ask a question.** Evidence discloses simple-rule historical results and crisis-check limits. The role-linked guide stays about the selected role and leaves the saved plan unchanged. Prepared guidance works without a live model.

## Definitions and limits

| UI evidence                             | Meaning to state                                                                                                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workforce median and pay range          | Gross annual pay for the stated employee population and year; excludes self-employment where labelled. This is not starting pay or an individual salary forecast.                                                   |
| Starting pay guide                      | An NCS starter-to-experienced range for the named example role. It does not specify a two-year outcome or every graduate's earnings.                                                                                |
| Real pay history                        | In 2024/25 money, using tax-year average CPIH. Missing or unreliable low-purity mappings create gaps; do not bridge the 2021 jobs coding break.                                                                     |
| Recent employment trend                 | Relative to the typical occupation during 2022–2025. A positive relative value can occur with falling absolute employment. Counts are indicative; neither the trend nor counts are live vacancies.                  |
| Automation exposure                     | Research about tasks, with coverage/range and mapping caveats; not a probability of job loss. Missing exposure is not silently imputed.                                                                             |
| Published sector scenario               | Retains the source's own horizon and geography. Sector growth is not a forecast for one occupation or a guarantee of entry-level hiring.                                                                            |
| Historical checks                       | Corrected simple tiers are assigned from base-year data before outcomes are scored. Windows overlap and those crossing 2021 compare pay only. The check does not validate the present slider or a learner's future. |
| 2008 and cost-of-living crisis measures | Failed placebo checks; excluded from recommendation inputs. Raw observations remain disclosed, without claiming validated resilience.                                                                               |
| Comparison score                        | An explicit weighted comparison of supplied evidence. It does not measure Amira's aptitude, admissions eligibility or probability of success.                                                                       |

The [ML v1.2 contract](../../packages/ml/CONTRACTS.md) and [owner's review fixes](../../packages/ml/README.md) define these measures. The wider Quiz supports 20 roles with preliminary interest affinities; Jobs has 412 evidence profiles. Keep those secondary features separate from the seven-role primary story.

## Rehearsal checks

- Direct subject and role URLs survive refresh: `#/computer-science`, `#/computer-science/3544`, `#/finance` and `#/finance/2421`.
- Evidence and Compare retain the selected occupation; moving a priority updates the recommendation without showing a stale result. Explain the actual winner rather than scripting a fixed one.
- Build my plan uses the chosen role and does not fabricate a completed interest profile. Direct CS/Finance pathways keep related-career suggestions within the supported seven groups; the secondary quiz retains its broader behavior.
- The role-specific guide shows prompts, question field and Send at 1200×800. A general guide with several roles still offers a chooser. Guide navigation does not replace the saved plan.
- Change career returns direct-plan users to the appropriate subject dashboard. Route changes, notes, tasks, saved links and export remain consistent after refresh.
- Chart/table alternatives, keyboard year inspection, focus, reduced motion, missing-history gaps and the 2021 break survive role/measure switches.
- Inspect sources and historical checks in the same release. Do not claim a failed placebo measure, synthetic development score or historical backtest validates personal recommendations.
- Rehearse external-provider failure while preserving local browser/API access; test failed local requests separately through visible retry controls.

Record screenshots, final integrated checks and unresolved limits in [VERIFICATION.md](../../apps/web/VERIFICATION.md). Prior checkpoint pass counts remain historical evidence; this page does not claim a fresh full-suite pass.
