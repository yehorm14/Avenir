# Prompt for Nazar's Claude (paste everything below the line)

How to use: clone the repo, open Claude Code in the repo root, paste the block below as your first message.

---

You are working on **Avenir**, a five-person GUTS Hackathon 2026 project (Aladdin by BlackRock challenge: "One app. One clear decision."). Avenir is a portfolio manager for a UK school leaver's future: it finds careers that fit, shows their return and risk with real UK data, says how sure it is, gives a hedge career, maps the route in, and shows how its past ratings held up. Code freeze is **Sunday 18 Oct at 11:30**. I am **Nazar**. With Yehor I own the backend. My half is the **decision engine** and the **FastAPI service**. Yehor owns the API contract, the catalogue and routes, and the live adapters (Adzuna, LLM); Arsenii owns ML and the data artefacts (`packages/ml`, `snapshots/ml`); two teammates build the frontend against our OpenAPI file.

## Read first, in this order (do not skip)
1. `AGENTS.md`: team rules. They override anything else, including this prompt.
2. `docs/backend-split.md`: who owns what, the seam between Yehor and me, the timeline.
3. `docs/superpowers/plans/2026-10-17-avenir-decision-and-api.md`: **my implementation plan (v2)**. 15 tasks, exact signatures, tests and rules. This is the work.
4. `packages/ml/CONTRACTS.md`: Arsenii's ML data contract (metric keys, flags, `MUST_MENTION`, backtest windows). Read-only for me.
5. `packages/contracts/avenir_contracts/`: `models.py`, `metric.py`, `data.py`, `ports.py`, `envelope.py`, `vocab.py`, `mock.py`. The contract in code. **Read-only for me**: if something is wrong or missing, open a PR comment to Yehor and keep going with a local workaround.
6. `docs/contracts.md` and `docs/superpowers/specs/2026-10-18-avenir-design.md` sections 1, 2, 4, 7, 8, for intent.

## Set-up (once)
```bash
git switch main && git pull
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest && ruff check .          # must be green before you start (contract tests)
cp context/_template.md context/nazar-backend.md
```

## How to work: superpowers, subagent-driven
- Use **superpowers:subagent-driven-development** to execute the plan: a fresh implementer subagent per task, a reviewer subagent after each task, and a whole-branch review before each PR. Follow **superpowers:test-driven-development** inside each task (failing test first, as the plan specifies). Use **superpowers:verification-before-completion** before claiming anything is done, and **superpowers:finishing-a-development-branch** for each PR.
- Run two tracks in parallel with **superpowers:using-git-worktrees** and **superpowers:dispatching-parallel-agents**:
  - Track A, worktree on branch `nazar/decision`: Tasks 1 to 10.
  - Track B, worktree on branch `nazar/api`: Tasks 11 and 12 now; Tasks 13 to 15 after Track A is merged into `main` (rebase first).
- **Model choice for subagents** (cost and speed matter tonight):
  - **Haiku** implementers: Tasks 1, 2, 6, 14 (mechanical, fully specified).
  - **Sonnet** implementers: Tasks 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 15 (rules and edge cases).
  - **Sonnet** for per-task reviewers (check against the plan's rules and the Review Focus list, not just "tests pass").
  - **Your main model** (Opus) only for orchestration, merges, and the final whole-branch review before each PR.
  - If a Haiku task fails review twice, redo it with Sonnet; don't loop.
- Give every subagent: the task text from the plan, its Interfaces block, the Global Constraints, the relevant contract file paths, and "follow AGENTS.md". Subagents must not edit files outside `packages/decision/`, `services/api/`, `docker-compose.yml`, `docs/openapi.json`, `context/nazar-backend.md`.

## Hard rules (from AGENTS.md, repeated because they matter most)
- No LLM, no I/O and no network in `packages/decision`. Pure functions, deterministic.
- Never fill a missing number. Missing → `None` / `Metric.missing`, confidence `low`; the UI says "missing".
- Every response uses the envelope; every metric keeps `source, year, region, granularity, n, confidence`.
- The app must run with **no API keys** on `snapshots/ml/mock/` + `snapshots/mock/` only. Live adapters come from `avenir_adapters.registry` when Yehor merges it; until then `deps.default_ports()` falls back to the contract defaults (the plan, Task 11, spells this out).
- Wording to users: "worth exploring", "automation exposure (research estimate)"; never "you should", "don't", "will disappear".
- Never commit secrets, `.env`, raw data, hostnames or IPs. Small commits, conventional messages (`feat(decision): ...`).

## Checkpoints (tell me, Nazar, at each; I will relay to Yehor)
1. Track A Tasks 1 to 6 green and Track B Tasks 11 to 12 green: push both branches, open **draft** PRs ("nazar: decision engine", "nazar: API skeleton"), body from `.github/pull_request_template.md`.
2. Track A complete: mark its PR ready for review. After it's merged, rebase Track B.
3. **01:00 target:** `uvicorn avenir_api.app:app --port 8000` serves the Amira flow on mock data: `POST /api/v1/profile` then `POST /api/v1/recommendations` with `{"profile": {"interests": ["maths","art_drawing","design","building_spaces"], "qualifications": [{"subject":"maths","level":"higher"},{"subject":"art","level":"higher"}], "nation":"scotland","automation_worry":0.5}, "first_idea": "architect"}` returns 1 to 3 picks (not Architect), a hedge or null, a roadmap, notices and an explanation. Export `docs/openapi.json` and tell the frontend.
4. Sunday 08:00 to 10:00: real `snapshots/ml/*.json` (Arsenii) and `snapshots/catalogue.json` (Yehor) land; no code change expected, fix what breaks, run Task 15 with `AVENIR_FREEZE=1`.

## Keep `context/nazar-backend.md` current
Status, tasks done, blockers, open questions, anything marked `(verify)`, the next step. Update it after every task, so another agent (or Yehor's Claude) can pick up your work cold.

## When you are unsure
Pick the simplest option that keeps the contract and the plan's tests, write the decision in the context file and the PR description, and carry on. Stop and ask me only if a change would alter `packages/contracts` or another person's folder.

Start now: read the files above, confirm in two or three lines what you will build first, then launch Track A Task 1 and Track B Task 11 in parallel.
