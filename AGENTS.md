# AGENTS.md: rules for every AI agent working on Pathfinder

Read this whole file before you write anything. It applies to every coding agent
(Claude, Codex, Copilot, Cursor, Gemini, any other) and to humans pasting agent output.
If this file and a task prompt disagree, this file wins; ask in your PR.

The full design is in `docs/superpowers/specs/2026-10-18-pathfinder-design.md`.
The API contract is in `docs/contracts.md`. Data sources are in `docs/data-sources.md`.

---

## 1. What we are building

**Pathfinder** (GUTS Hackathon 2026, Aladdin by BlackRock challenge: "One app. One clear decision.")
is a portfolio manager for your future. For a UK school leaver it finds careers that fit,
shows their return and risk with real UK data, says how sure it is, gives a hedge career,
maps the path in, and publishes how its own past ratings held up (the backtest).

- **User:** Amira, 17, S6 at a Glasgow school. Good at maths and art, first idea "architect",
  worried AI will hit the jobs she likes.
- **Decision:** which career to aim for, and what her next step into it is
  (subjects, route: degree, graduate apprenticeship, college).
- **Picks:** Ambitious (highest return among good fits), Safe (lowest risk among good fits),
  Balanced (best return per unit of risk). Each compared against her first idea.
- **Never cut:** three cards vs first idea, the hedge, the backtest button, the roadmap,
  provenance badges, pull-the-plug.

Deadline: code freeze **Sunday 18 Oct, 11:30**. A working end-to-end demo beats extra features.

## 2. Non-negotiable rules

1. **No LLM in ranking.** Fit, return, risk, picks, hedge and roadmap are pure, deterministic,
   unit-tested Python in `packages/decision/`. No I/O and no network in that package.
2. **Provenance on every number.** Every metric is
   `{value, low, high, source, year, region, granularity, n, confidence}`.
   A number without a source does not ship.
3. **Missing means missing.** Never fill a gap with a guess, an average or an LLM. Return the
   metric as missing, lower the confidence, and let the UI say "missing".
4. **Never invent data values, codes or URLs.** If you could not check something, write
   `(verify)` next to it and list it in your PR description.
5. **Only adapters touch files or the network.** One folder per source in
   `packages/adapters/<source>/`, each with a committed snapshot fixture. Live calls:
   3 s timeout, 1 retry, then the snapshot with `meta.sources[].status = "snapshot"`.
   The demo must run from `docker compose up` with **no API keys present**.
6. **Backtest honesty.** A feature for year Y may only read data published for Y or earlier.
   Every backtest change needs a test proving no look-ahead. Bad results are shown, not hidden.
7. **Wording for a 17-year-old.** "Automation exposure (research estimate)", never
   "AI will take this job". "Worth exploring", never "you should" or "don't".
   Exposure is not job loss.
8. **Coverage labels.** England-only data (Skills England sector assessments,
   Find an Apprenticeship) is shown with an "England" label; Occupations in Demand is
   "UK (some indicators GB)", see `docs/data-sources.md`. Group-level data
   (wellbeing, stress) is shown with a "job group" badge, never as occupation-level.
9. **Forbidden sources:** WRDS, Interactive Brokers, LMI for All (closed),
   scraping company career sites, anything whose licence we have not checked.
10. **Secrets** only in `.env` (gitignored). Commit `.env.example` with empty values.
    Nothing secret in the frontend, in snapshots, in logs or in PR text.
11. **Raw data is never committed.** It lives in `data/raw/` (gitignored) and is listed in
    `data/manifest.yaml`. Only small derived files (< 1 MB each) go in `snapshots/`.
12. **Stay in your lane.** Do not edit another slice's folder or `docs/contracts.md`.
    Contract changes go through a PR to the contract owner with the box ticked in the template.

## 3. Who owns what

| Slice | Folder | Owner |
| --- | --- | --- |
| ML and training (M1 to M6, backtest) | `packages/ml/` | Arsenii |
| Data ETL (`careers.json`, curated routes) | `packages/adapters/`, `scripts/fetch/`, `data/manifest.yaml` | TBD |
| Backend API | `services/api/` | TBD |
| Decision logic | `packages/decision/` | TBD |
| Frontend and glue | `apps/web/`, README, diagram, pitch | TBD |
| Contract | `docs/contracts.md` | Yehor |

Humans fill in TBD. Agents do not change this table.

## 4. Stack

- Backend: Python 3.12, FastAPI, Pydantic v2, pandas, pytest, ruff.
- Frontend: React + Vite + TypeScript, client types generated from the OpenAPI schema, ESLint, Prettier.
- ML: PyTorch (laptop `torch-cuda` env or the cluster), sentence-transformers, scikit-learn.
- Data: JSON artefacts loaded at start, no database. `careers.json` plus
  `backtest.json`, `hedge.json`, `demand.json`, `exposure.json`, `matcher_eval.json` in `snapshots/`.
- Run: `docker compose up` or `make run`. `make test` runs everything.

## 5. How to work

1. **Branch** from `main`: `<name>/<topic>`, e.g. `arsenii/backtest`, `agent-ml/hedge`.
   Never commit to `main` directly.
2. **Context file.** Copy `context/_template.md` to `context/<name>-<topic>.md` and keep it current:
   status, what you did, what is blocked, open questions. This is how the next agent picks up.
3. **Small PRs**, opened as drafts, using `.github/pull_request_template.md`. One concern per PR.
4. **Tests first** for anything in `packages/decision/` and for the backtest.
5. **Before you push:** run `make check` (lint, tests, secret scan) and read your own diff for
   secrets, IP addresses, cluster hostnames, personal names other than team first names,
   and leftover template placeholders.
6. **Linking work:** after opening a PR, a human adds `→ <name> #<PR>` to the tracking issue.
   Agents do not edit issues.
7. **When unsure:** write the question in your PR description and context file, pick the
   simplest option that keeps the contract, and carry on. Do not stop silently.

## 6. Definition of done

- Lint clean, tests added and passing, `make check` green.
- Every new number has provenance; every new source is in `data/manifest.yaml` with licence.
- Behaviour a user can see is described in the README section for your slice.
- Your context file says "ready for review" and lists anything marked `(verify)`.

## 7. Attribution we must show

"Jobs by Adzuna"; ONS (Open Government Licence); Skills England / DfE (OGL);
ILO Working Paper 140 (Gmyrek et al., 2025); ESCO (European Commission);
HESA / Discover Uni (CC BY 4.0); O*NET (CC BY 4.0) if used.
Check each licence on download and record it in `data/manifest.yaml`.

## 8. AI use disclosure

Every AI-written sentence in the app is labelled "AI-written, check the source".
The README's AI section lists where the app uses AI and which coding agents built it.
