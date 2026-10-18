# Avenier: the speech (what to say)

About 650 words for 6:30. Plain English. Read the numbers from the screen if they differ from this page. Never "you should"; say "worth exploring". Say "history, not a forecast".

---

## Block 1, 0:00 to 1:30. Frontend (Illia or Max)

Hi, we are Team 18, and this is Avenier.

Meet Amira. She is 17, in S6 in Glasgow. She is good at maths and art, her first idea is architect, and she is worried about AI. Today her information is spread across pay tables, careers sites and TikTok. Avenier puts it in one place and gives her one clear decision: which career to explore first, and what to do about it this month.

*(click Try architect)*

One click sends her answers to our API. Her priorities become weights: interest 55, pay 15, demand 30 percent. Her own idea stays first.

*(click Your matches)*

Next to it, the app puts alternatives: IT business analyst, and actuary, economist or statistician. And it is honest about her first idea: architect pay has been falling against the typical job.

We never just hand her the popular or best-paid role. The picks come in three kinds: ambitious, balanced and lower risk, plus a hedge career that shares her skills but held up better. A risk-averse student gets a low-volatility option on the same screen, with the reasons.

Arsenii will show you where every number comes from.

## Block 2, 1:30 to 4:00. Arsenii: data, sources and ML

*(Explore finance, scroll to Statistics for this role)*

Every figure on this page carries its source and its year. Finance and investment analyst: fifty thousand pounds median pay, full-time employees, 2025, provisional, from the ONS Annual Survey of Hours and Earnings.

The pay history is deflated with CPIH, so this is real pay in 2024/25 prices, not nominal. The dashed years use older occupation codes; the 2021 code change is marked, not hidden.

Automation exposure comes from ILO Working Paper 140, cross-checked against the Department for Education index: a Spearman correlation of 0.78 across 400 occupations. It is a research estimate of tasks, not a probability of losing a job, and the screen says so.

*(Hedge careers)*

Hedges come from shared ESCO skills: careers that overlap with this one and held up better in the data. The panel shows how many skills they share.

*(Crisis checks)*

Crisis checks have a placebo test. COVID passes. Cost of living and the 2008 crisis fail, so they are excluded from recommendations. We show the failures instead of hiding them.

This is the point of the risk side. The same rules give general specifications for any occupation, not a story about a few popular jobs. Pay history, employment volatility and how an occupation behaved in past shocks feed a risk score, so next to the exciting choice there is always a steadier, lower-volatility one, and the student sees why.

*(Home, BlackRock card)*

Employers get the same treatment. BlackRock's card uses its own filings: about 24,900 employees at the end of 2025, from the 2026 proxy, page 37. The UK salary ranges are self-reported on Glassdoor and labelled as such. Ways in for a school leaver come first: Smart Start for 16 to 24 year olds, and an analyst programme open to any degree subject.

*(if time: My plan, The evidence, 2019 to 2024)*

And we tested ourselves. Simple rules, judged on later outcomes: in the 2019 to 2024 window, the top third by pay lost 6.4 percent in real pay; all occupations lost 0.9. A bad result for the naive rule, and we show it.

## Block 3, 4:00 to 5:15. Backend (Nazar or Yehor)

*(the /docs tab)*

The API came first. Every endpoint is in OpenAPI, and every answer uses one envelope: data, error, and meta with a request id and the status of each source.

*(repo folders)*

Three layers. apps/web is the interface. packages/decision is pure rules: no network, no model, fully unit-tested. packages/adapters and the app API bring the data in, each source behind its own adapter with a snapshot fallback.

773 tests, zero failures. Linting and a secret scan on every change. Keys live only in a local .env; the committed example has empty values.

*(Wi-Fi off, F5, Try architect)*

Now I pull the plug. No network. The same plan loads from committed snapshots, and anything live, like job adverts, is labelled missing rather than faked.

## Block 4, 5:15 to 6:15. Arsenii: the chatbot and what stays human

*(Wi-Fi on, Chatbot, Actuary, type the question)*

The last piece is the chatbot, and here is the rule we built it on: the ranking never touches the language model.

When Amira asks a question, the model does not answer from memory. It calls our own tools: the role's statistics, the career path, the employer facts. It writes only from what those tools return. Then we check every number in its reply against the evidence; if one is not there, the student gets a prepared answer instead, labelled as such. Phrases like "you should" are blocked. With no key, or no network, the prepared answers are what you get. It is the same honest fallback you saw offline.

*(point at the badge and the links)*

So the AI explains. It never decides.

## Block 5, 6:15 to 6:30. Close

*(slide)*

One user, one decision, every number with its source, and a fallback for everything. Avenier. Team 18. Thank you for your attention.

---

## Three answers to have ready

**"Is an LLM ranking careers?"** No. The ranking is deterministic code in packages/decision, with no network access. The model only writes explanations, from tool results, and every number is checked.

**"Why not just show the popular, best-paid roles?"** Because that is what every careers site already does. We score fit, return and risk for every occupation with complete data, then give an ambitious, a balanced and a lower-risk pick, plus a hedge. The risk-averse student gets a real choice.

**"What is not finished?"** The human-verified catalogue is incomplete, so one freeze check fails and we say so. Matcher accuracy is measured on synthetic profiles only. Licence sign-off is still a human task. Everything on screen is history with a source, never a forecast.
