# Three-minute demo: Amira and architect

**Amira is 17, in S6 at a Glasgow school. She is good at maths and art, her first idea is "architect", and she is worried AI will hit the jobs she likes. The decision is which career to aim for and what her next step into it is.**

This follows [AGENTS.md section 1](../../AGENTS.md). The Computer Science and Finance journey is a [secondary journey](cs-finance-demo.md) and is not part of this timed run.

## Before the clock starts

- Start the app with the [launch commands](README.md#run-and-verify) (`node scripts/run-app.mjs --production`), with no API keys set.
- Use a fresh browser profile so Home shows the Amira card. Rehearse at 1200x800.
- Rehearse the last step (pull the plug) once, so you know where the app shows its snapshot badges.

## Timed run

| Time      | Action                                                                                                                                  | What to say                                                                                                                                                                                                     |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00-0:20 | On Home, read the **Amira** card, then click **Try architect**.                                                                        | "Amira is 17, in S6 in Glasgow. She likes maths and art, thinks architect, and worries about AI. One app, one clear decision: which career to aim for." The answers are prefilled from her story.            |
| 0:20-1:15 | In **My plan**, open **Compare the trade-offs**. Read the three picks (High earnings, Lower risk, Balanced) next to her first idea.    | Each pick is compared with architect on interest fit, earnings index and combined risk. These are fixed rules, not an LLM and not a forecast. Say which careers appear in the actual build; do not script them. |
| 1:15-1:35 | Point to the **hedge** career under the picks.                                                                                          | A hedge is a second career that shares skills with a pick but carries different risk. It is a way to spread her bets, labelled with its evidence status.                                                     |
| 1:35-2:10 | Open **The evidence**, then **How simple rules held up** (the backtest).                                                                | The rules only read data published for the year they rate. Weak and negative results are shown, not hidden. Windows overlap, and it does not validate Amira's personal outcome.                              |
| 2:10-2:30 | Open the **route** page for her chosen career and read the next step.                                                                   | The roadmap shows subjects and routes (degree, graduate apprenticeship, college) for Scotland, and the next step. Check current entry requirements; these are examples.                                      |
| 2:30-3:00 | **Pull the plug.** Disconnect the network (Wi-Fi off, or unplug), then reload Home and click **Try architect** again.                  | See below. Say what you actually observe.                                                                                                                                                                       |

## Pull the plug, honestly

The app and its API run on this laptop and read committed snapshots, so with the network disconnected the comparison, hedge, backtest and roadmap should keep working. Show the source badges: they say **snapshot**, not live. This build has **no live job adverts**; do not claim any. Source websites and external links still need internet. If the local API is itself unreachable (for example DevTools global Offline blocks it), the app shows its error and Try again state; say so rather than calling it proof of offline mode.

Automation exposure is a research estimate, not a prediction of job loss. Wording to use: "worth exploring", never "you should" or "don't".

## Answers for judges

- **What decision is clearer?** Which career Amira aims for next to her first idea, and her next step.
- **Is an LLM ranking careers?** No. Fit, return, risk, picks and hedge are deterministic rules. AI-written text is labelled.
- **How did the rules hold up?** Show the backtest panel; state only what is on screen.
- **Is the data live?** No. Snapshots, with the source and year on each number.
