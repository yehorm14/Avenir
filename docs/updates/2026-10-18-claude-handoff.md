# Handoff: what Claude did for Yehor's slice, and what is left (Sun 18 Oct, 09:50)

For: the next agent (and the team). Freeze is **11:30**. `main` is protected (PRs only, squash-merge only).

## 1. State of `main` (b397851)

- **Product "Avenier"** runs from one key-free command: `bash scripts/setup.sh && node scripts/run-app.mjs --production` → http://127.0.0.1:4175.
  - **Frontend** (`apps/web`): Home leads with Amira's "Try architect" journey: three picks vs her first idea, hedge, evidence, backtest, roadmap. CS/Finance is a secondary journey. Also: the Jobs catalogue (412 careers), My plan with export, Sources panels with the required attributions.
  - **Backend:**
    - canonical API (`services/api`, Nazar);
    - decision engine (`packages/decision`, Nazar);
    - contract v2.1 (`packages/contracts`, Yehor);
    - live adapters with hard 3 s deadlines and fallbacks (`packages/adapters`, Yehor);
    - catalogue/routes ETL (`packages/etl`, Yehor);
    - Arsenii's **real ML v1.2** artefacts (`packages/ml`, `snapshots/ml`).
- **Checks:** pytest 477 passed, 3 skipped; ruff clean; web tests 26/26, build OK, npm audit 0; secret scan clean (2 verified false positives ignored in `.gitleaksignore`).
- `AVENIR_FREEZE=1 pytest` fails **only** `test_no_mock_at_freeze`. This is by team decision: the catalogue and routes ship as labelled sample data.
- **Honesty checks verified in code:** no backtest look-ahead (F01); no averaged-in exposure (F06); every one of 5,200 valued metrics has a source, as_of and confidence.

## 2. What I did (Saturday 21:00 → Sunday 09:50)

| PR | What | Why |
| --- | --- | --- |
| #3 | Catalogue + routes ETL: verified-CSV loader, build CLI, Excel-proof CSV handling, manifest entries | The display catalogue must never show unverified data; failures name the row |
| #4 | Contract v2.1: ML v1.1 fields, `first_idea_candidates`, 422/404 rules, 5 MB rule for `snapshots/ml` | Adopt Arsenii's v1.1 without breaking anyone; Nazar's "Did you mean...?" |
| #5 | Live adapters: registry, Adzuna (hard 3 s deadline, breaker, snapshot fallback), LLM explanation (numbers/notices/wording checked, template fallback) | The app must run with no keys and never stall on stage |
| #6, #15 | Frontend pack `docs/frontend/` (README, schemas, generated examples), matched to the live API | The frontend could build before the API existed |
| #11 | Pull-the-plug rehearsal harness `scripts/demo/pull_the_plug.py` | Shows honest live/snapshot/mock badges; fails loudly |
| #12, #13 | Team plans (frontend, ML pipeline) | Shared, written source of truth |
| #17, #18 | Context file `context/yehor-backend.md` | The handoff record |
| #20 | Security fix (prototype file containment) + exposure-confidence fix, test made data-independent | Two fixes the final delivery had lost |
| #21 | Required source attributions in the app; internal details scrubbed | AGENTS.md sections 7 and 8, before a public URL |
| #22 | Demo leads with Amira's architect journey | Team decision; AGENTS.md section 1 |
| #23 | Cold install works: npm lockfile, Windows setup path, scanner false positives, symlink-test skips | Hosting from a fresh clone was broken |

I also:
- verified and merged Nazar's #8, #9, #14 (each against a live API);
- merged Arsenii's #10;
- closed #2 and #19 (both contained in `main`);
- deleted 21 stale branches;
- made the repo squash-only and protected `main`.

## 3. Rulings I made on the team's behalf (each with what it costs if wrong)

1. **R1/R2:** Adzuna and LLM calls get a 3 s total budget, retry included. Cost if wrong: more fallbacks under latency (safe).
2. **R3:** `writer_from_env()` picks the LLM or the template from env. Cost if wrong: one extra public function.
3. **R4:** wellbeing and stress are always missing (no parser, no data). Cost if wrong: two parameters to add later.
4. **R5/R6:** the OiD parser is deferred and lazily imported; the CLI writes the catalogue first. Cost if wrong: none (OiD never arrived).
5. **R7:** the catalogue's `ads_now` is missing; the API overlays the live value. Cost if wrong: ads show "missing" without keys.
6. **R8:** real catalogue/routes are labelled `preliminary`, never `mock`. Cost if wrong: a label.
7. **R9:** the registry reads `.env` on first use, never at import. Cost if wrong: a tiny file read.
8. **R10:** the LLM check rejects "you should"/"don't". Cost if wrong: more template fallbacks.
9. **R11:** a 60 s Adzuna breaker after outage or auth/quota errors. Cost if wrong: up to 60 s of snapshot after recovery.
10. **R12:** the catalogue PR shipped without Task 5 (OiD). Cost if wrong: one extra PR later.
11. **R13/R14:** the frontend pack was regenerated only after #4 (after the user approved the merge); snapshots/mock were not regenerated. Cost if wrong: one regeneration.
12. **R15:** single-task branches used the task review as the whole-branch review. Cost if wrong: one less independent pass.
13. **R16:** dropped the generic alias "technician". Cost if wrong: typed "technician" is now ambiguous.
14. **R17–R19:** a demo harness instead of live ads (no keys); 127.0.0.1 as the default; a 5xx or empty data is a FAIL. Cost if wrong: an honest "missing" on stage.
15. **R20:** Saturday night's merges used merge commits (dependent branches). Squash-only applies from Sunday morning. Cost if wrong: noisier history.

**User decisions recorded:**
- release-based delivery with Arsenii's v1.2 winning in ML;
- merge target `codex/final-delivery` plus two fixes;
- keep the architect story;
- ship the sample catalogue labelled;
- laptop + tunnel hosting by Illia;
- no new pull-the-plug feature.

## 4. Known limits (say them honestly)

- Job names, subjects and routes are **sample data** (labelled). `verified_by` is not filled in `data/curated/occupations.csv`.
- **No live job ads** (no Adzuna key) and **no AI-written text** (no LLM key; the template is used). Pull the plug = disconnect the network; the app keeps working on snapshots.
- Interest matching is preliminary (labels not scored). The backtest uses simple rules, not our picks. AI exposure is a research estimate, not job loss. Pay is the median for adult employees.
- **Licences:** all 17 manifest entries have an empty `licence_checked_by`; 5 are marked (verify). The ILO entry is inconsistent: the manifest says "ILO terms", `sources.json` says CC BY 4.0.

## 5. What is left (roles, until 11:30)

| Who | Task |
| --- | --- |
| Illia | Host: `git pull`, setup, `run-app.mjs --production`, `cloudflared tunnel --url http://127.0.0.1:4175`; browser click-through of "Try architect"; one offline run |
| Yehor | Present: rehearse `docs/launch/demo-script.md` twice, under 3 minutes |
| Nazar | Backend on call; skim #20 and #21 (they touched his decision package and `apps/web`) |
| Arsenii | Settle the ILO licence; confirm the 3 ML files that differ from #19; Q&A notes on data caveats |
| Maksym | Slides: architecture diagram + screenshots |
| Next agent | See section 6 |

## 6. Delegation prompt for one agent

```
You are the final-delivery agent for Avenir (repo C:/dev/Avenir, GitHub yehorm14/Avenir). Code freeze is 11:30 today.
Read first: AGENTS.md, docs/updates/2026-10-18-claude-handoff.md (this file), docs/launch/README.md,
docs/launch/demo-script.md. main is protected: work on a branch, open a PR, squash-merge only after tests pass.
Never invent values, codes or URLs; missing stays missing. No new features: only fix real breakages.

Do, in order:
1. Fresh clone check: in a new folder, clone main, `bash scripts/setup.sh`, `bash scripts/check-setup.sh`,
   `node scripts/run-app.mjs --production`. Walk the Amira "Try architect" journey over HTTP (and in a browser if one is
   available): three picks vs first idea, hedge, evidence/backtest, roadmap, Jobs, Sources/attribution panel.
   Report anything broken with the file and owner.
2. Run the gates: `pytest`, `ruff check .`, `AVENIR_FREEZE=1 pytest` (only test_no_mock_at_freeze may fail),
   `npm --prefix apps/web ci && npm --prefix apps/web test && npm --prefix apps/web run build`, `make secrets` if make exists.
3. Run `python scripts/demo/pull_the_plug.py --base-url http://127.0.0.1:<canonical API port>` against the canonical API
   (start `uvicorn avenir_api.app:app --port 8000` if the app doesn't expose it) and paste the summary.
4. Build the submission: `python scripts/package_submission.py`, then install and run that archive from scratch once.
   Don't commit the archive.
5. If anything in steps 1-4 fails: smallest fix on a branch, PR, squash-merge after green tests; tag the owner
   (apps/web, scripts = Illia; packages/decision, services/api = Nazar; packages/ml, snapshots/ml = Arsenii;
   contracts, adapters, etl, docs/frontend = Yehor).
6. Before 11:15, post a one-paragraph status for the team: URL (from Illia), how to run locally, the gate results,
   known limits (section 4 of the handoff).
```
