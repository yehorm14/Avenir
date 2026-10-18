# Three-minute demo

**Amira is 17, lives in Glasgow and enjoys maths. She is choosing between Computer Science and Finance. The decision is which role to explore first and what to try this month.**

Show an evidence-backed recommendation that changes with her stated priorities, then a route and a saved action. The broader quiz and 412-profile directory are secondary; the primary demo stays with the seven supported CS/Finance occupation groups.

## Before the clock starts

- Start the app using the [launch commands](README.md#run-and-verify). Use the exact final integrated build with optional keys empty.
- Use a dedicated browser profile with a fresh plan. Keep a second tab with a saved Amira plan for recovery, without deleting anyone's progress.
- Rehearse at 1200×800 or the presentation display's actual dimensions. Check keyboard focus, Compare, plan persistence, export and the historical checks panel.
- Rehearse with external internet unavailable while keeping the local API reachable. Source websites still need internet. State the actual verification result recorded for this release; do not reuse an older test count.

## Timed run

| Time      | Action                                                                                                                                                                                                          | What to explain                                                                                                                                                                                                                                                                                                                                        |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0:00–0:20 | From Home, open **Explore CS**.                                                                                                                                                                                 | “Amira likes maths and is choosing between computing and finance. We will help her choose a first role to explore and one practical next step.” No questionnaire is required for this direct comparison.                                                                                                                                               |
| 0:20–0:45 | In **Evidence**, inspect Software developer, then Data analyst. Point to pay, employment, automation research and the separate Starting pay guide.                                                              | ONS workforce median pay is not a graduate salary. The NCS guide describes an example role; ILO task exposure is not a probability of job loss. Each observation keeps its date, range and limitations.                                                                                                                                                |
| 0:45–1:20 | Open **Compare careers**. Move the Pay / Employment trend slider, using **Higher pay**, **Employment trend** and **Balanced** as useful shortcuts. Read the actual first-role recommendation and its trade-off. | The recommendation responds to Amira's explicit weights and stays within this subject. There is no inferred interest profile. Employment trend is relative historical performance in 2022–2025, not future vacancies; a positive relative result can still mean falling absolute jobs. Do not promise a particular winner before checking the release. |
| 1:20–1:45 | Open **Finance**, inspect analyst/accountant evidence and its **Compare careers** result. Choose which recommendation Amira wants to explore first.                                                             | Combined information makes the decision clearer than separate salary and research pages. Amira controls the priorities and final choice; a score is not personal suitability or a forecast.                                                                                                                                                            |
| 1:45–2:20 | Choose **Build my plan**. Compare **University** and **Earn & learn**, then open **My plan**. Add a short reason, choose a practical action and download the plan.                                              | The decision becomes a route and something she can try. Mark an action complete only if actually done during rehearsal; choosing it is not completing a course, application or event. Saved notes, route and progress should match the export.                                                                                                         |
| 2:20–2:40 | Open **The evidence** from the plan workspace navigation. Show **How simple rules held up** and the crisis-check limitations.                                                                                   | Historical tiers use base-year inputs and later outcomes. Windows overlap; comparisons crossing 2021 are pay-only. The 2008 and cost-of-living measures failed placebo checks and are excluded from recommendations. These checks do not validate Amira's personal outcome or the current slider.                                                      |
| 2:40–3:00 | Ask the selected role's prepared guide about pay or routes. Inspect any sources, then refresh or return Home and resume the plan.                                                                               | No live language model or account is required. Source coverage is explicit; current course requirements still need checking. The chosen route and next action remain saved in this browser.                                                                                                                                                            |

Suggested plan note: `Compare a computing course with a finance course, check their entry requirements, and try a small task from each before deciding.`

Pick one real next action: a small app/data exercise for CS, or explaining a company's revenue, operating profit and cash flow for Finance. Use the action belonging to the actual selected role. Course and opportunity links are discovery resources, not confirmed openings or eligibility decisions.

## Evidence wording to rehearse

- **Real pay:** “In 2024/25 money, using tax-year average CPIH.” Low-purity historical mappings and missing observations create gaps; the 2021 occupation-code break matters.
- **Employment trend:** “Faster or slower than the typical occupation during 2022–2025.” Positive relative performance does not necessarily mean absolute employment grew.
- **Historical checks:** “Simple rules evaluated later, not our personalised recommendations.” Show weak or negative evidence alongside strong results; failed placebo checks are not validated resilience signals.
- **AI:** “Offline embedding affinities support the secondary interest matcher. The primary comparison uses deterministic rules. The guide uses prepared information; no live model is needed.” Synthetic development labels do not establish learner matching accuracy.

## Resilience and recovery

Keep local servers reachable when demonstrating external-provider failure. DevTools' global Offline mode can block the local API too; use that deliberately to show the app's error/retry state. Do not describe a failed local API request as proof that snapshots require external internet.

If a provider is unavailable, show its labelled snapshot or missing state. If a local request fails, use the visible retry action. If the stage environment interrupts the journey, switch to the prepared second tab, say it contains a saved plan, and continue. Never substitute invented live results.

## Answers for judges

- **What decision is clearer?** Which CS/Finance role Amira wants to explore first, based on her priorities, followed by a practical next step.
- **Why combine data?** Earnings, observed employment, automation research and training examples answer different questions. The comparison explains their trade-offs in one path to action.
- **What is personalised?** The primary comparison uses Amira's explicit pay/employment priorities. It does not infer interests, admissions eligibility or personal success.
- **How broad is it?** The primary comparison covers seven CS/Finance occupation groups. The secondary quiz matches across 20 roles; Jobs browses 412 supplied profiles with variable evidence and route coverage.
- **What has been validated?** State only the final integrated verification recorded by the release owner. Historical rule checks and synthetic matcher development results do not establish real-learner recommendation accuracy.
- **Could it become a business?** A school/adviser pilot could test evidence understanding and action follow-through. Proposed pricing, adoption and adviser tools remain [hypotheses](business-case.md), not existing traction.
