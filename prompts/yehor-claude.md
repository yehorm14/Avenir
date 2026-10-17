# Prompt for Yehor's Claude in VS Code (paste everything below the line)

How to use: in VS Code open `C:\dev\Avenir`, run the set-up block below in the terminal, then open Claude Code and paste the block below the line as your first message.

```powershell
git fetch origin
git switch main; git pull          # after PR #1 is merged (otherwise: git switch yehor/wave0-contracts)
python -m venv .venv; .venv\Scripts\activate
pip install -e ".[dev]"
pytest                             # 32 passed expected (19 ML + 13 contract)
```

---

You are working on **Avenir** with me, **Yehor**, in this repo. GUTS Hackathon 2026, Aladdin by BlackRock challenge ("One app. One clear decision."). Avenir is a portfolio manager for a UK school leaver's future: careers that fit, return and risk from real UK data, confidence on every number, a hedge career, the route in, and a published track record. Code freeze is **Sunday 18 Oct at 11:30**.

Team: **Nazar** builds the decision engine and the FastAPI service (his Claude has `prompts/nazar-claude.md`). **Arsenii** owns ML and the data artefacts (`packages/ml`, `snapshots/ml`). Two teammates build the frontend. **I own** the API contract (`packages/contracts`), the catalogue and routes ETL, and the live adapters (Adzuna, LLM explanation, tag suggester).

## Read first (in order)
1. `AGENTS.md`: team rules; they override this prompt.
2. `docs/backend-split.md`: the seam between Arsenii, Nazar and me, and the timeline.
3. `docs/superpowers/plans/2026-10-17-avenir-data-and-adapters.md`: **my plan (v2), 6 tasks**.
4. `packages/ml/CONTRACTS.md` (Arsenii's ML contract, read-only for us) and `packages/contracts/avenir_contracts/` (my contract code: `metric.py`, `models.py`, `catalogue.py`, `data.py`, `ports.py`, `vocab.py`, `mock.py`).
5. `docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md` (Nazar's plan), only so you know what the API expects from my registry.
6. `context/yehor-backend.md`: where I left off.

## How we work: plan first, then subagents
1. **Before writing any code**, summarise in 10 lines or fewer: what you will build tonight, in what order, which tasks run in parallel, which model each subagent gets, and anything in the plan that looks wrong against the code. Then **wait for my "go"**.
2. Execute with **superpowers:subagent-driven-development**: one fresh implementer subagent per task, a reviewer subagent after each, a whole-branch review before the PR. Inside each task follow **superpowers:test-driven-development**. Use **superpowers:verification-before-completion** before saying anything is done, and **superpowers:finishing-a-development-branch** for the PR.
3. Parallel where independent (**superpowers:dispatching-parallel-agents**, worktrees via **superpowers:using-git-worktrees**): Tasks 1+2+3 (registry, Adzuna, LLM) on `yehor/live-adapters`; Tasks 4+5+6 (catalogue, shortage, routes) on `yehor/catalogue`.
4. **Models:** Haiku for Tasks 1 and 5 and fixture-making; Sonnet for Tasks 2, 3, 4, 6 and for every reviewer; your main model only for orchestration, merges and the final review. If a Haiku task fails review twice, redo it with Sonnet.
5. Every subagent gets: its task text and Interfaces, the plan's Global Constraints, the contract file paths, and "follow AGENTS.md; only edit packages/adapters, packages/etl, packages/contracts, scripts/fetch, data/, context/yehor-backend.md".

## Hard rules
- Never invent a value, SOC code, URL or route. Missing → `Metric.missing(...)`; the UI says "missing".
- Live adapters: 3 s timeout, 1 retry, never raise, snapshot fallback. The app must run with no keys.
- LLM text: only numbers present in the response, and every `rec.notices` sentence verbatim; otherwise the template.
- No secrets, `.env`, raw data, hostnames or IPs in commits. Small conventional commits.
- Contract changes (`packages/contracts`) need Nazar's agreement in the PR; regenerate `snapshots/mock/` and tell him.

## Things only I (the human) can do; ask me when you reach them
- Adzuna app id and key in `.env`.
- The LLM endpoint (ELM base URL, key, model).
- Filling `verified_by` (and descriptions) in `data/curated/occupations.csv` and writing `data/curated/routes.csv` from real pages.
- The Occupations in Demand download (Explore Education Statistics, "Download all data").

## Checkpoints
- Tasks 1 to 3 merged → tell Nazar the registry is live (his API picks it up with no change).
- 01:00: the API on mock data plus my live adapters gives the full Amira flow; pull-the-plug works.
- Sunday 08:00 to 10:00: real `snapshots/catalogue.json` and `routes.json`; `AVENIR_FREEZE=1 pytest` green.

Keep `context/yehor-backend.md` current after every task. Start by reading, then give me the summary and wait.
