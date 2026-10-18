# arsenii: final integration check, ML docs and role statistics (Sun 18 Oct)

- **Owner:** Arsenii (human) / Claude Code (agents)
- **Branch:** `arsenii/final-local`, stacked on `codex/final-delivery` (Illia's integrated delivery)
- **Status:** ready for review; see the PR

## What this branch adds
| Area | Change |
| --- | --- |
| Windows | `npm ci` works again (lock file lacked five optional rollup platform entries). Three symlink tests skip, with the reason, on Windows accounts that cannot create symlinks. Windows run steps in the README and launch docs. Measured verification in `apps/web/VERIFICATION.md`. |
| ML licence | The exact ILO CC BY 4.0 adaptation disclaimer and DOI for Working Paper 140, in the pipeline (`ml_common.py`), `snapshots/ml/sources.json`, the mock copy, `docs/data-sources.md` and the README. |
| ML docs | `packages/ml/README.md` explains every backtest `group_then` value (ambitious, safe, other, balanced, all), quoting the rules in `assign_tiers`. Nazar asked for this. |
| Manifest | `data/manifest.yaml`: checked URLs and licences (ONS CPIH, SOC pages, DfE annex, ONS job adverts, APS age bands, O*NET, NCS job profiles). `licence_checked_by` stays empty for a human. Yehor owns `data/`; please review. |
| Wording | The matcher note shown on The evidence page now reads in plain English (pipeline and snapshots). |
| Role statistics | `GET /api/careers/{soc}/evidence-pack` and a "Statistics for this role" panel (hedges, historical rule checks, crisis checks, interest fit, pay history), each number with its source and caveats. |
| Grounded guide | `POST /api/guide` answers from the evidence pack when a model is configured (`LLM_*` or `ANTHROPIC_API_KEY` in `.env`), with the same hard number checks as the explanation writer; otherwise the prepared template, labelled as such. |

## Verified on Windows 11 (Node 24, npm 11, Python 3.13), commit c8810a6
Core 467 passed / 3 skipped; app and integration 117 passed / 3 skipped; prototype 32; web 26; ruff and the secret scan pass. `format:check` fails only because of CRLF checkouts (`--end-of-line auto` passes). Docker not run. Details in `apps/web/VERIFICATION.md`.

## Demo rehearsal (every scripted step passed; no console errors)
Problems a judge may notice, ranked, for the UI owner:
1. Guide: "What are the routes into this career?" on Actuary (2433) returns a data-scientist pathway example with no sources. For the pitch, ask the guide about **pay**, not routes.
2. The evidence page says "three priority sliders" and "Ambitious, Balanced and Safe picks"; the demo shows one slider with Higher pay / Employment trend / Balanced. An empty card "No simple-rule version — 0 — Not comparable" also shows.
3. The source list shows Census as "pending" (honest, but reads as unfinished).
4. "Build my plan" from the Finance comparison builds the plan for the recommended role (Actuary) even while viewing Accountant, and its "Try the work" step is a data-analyst task.
5. My plan has only "done" checkboxes; there is no way to choose an action without marking it complete.
6. "Your pay scenario £33,075" can read as a forecast.

## Blocked on (humans)
- `AVENIR_FREEZE=1 pytest` still fails `test_no_mock_at_freeze`: `snapshots/catalogue.json` and `routes.json` do not exist. That is the 09:30 build from the curated CSVs (`python -m avenir_etl.build`), Yehor's step. `main` has not moved since 00:23.
- A model key in `.env` if the live guide is wanted in the demo. Without it the guide stays prepared and says so.

## Marked (verify)
- Manifest: ESCO licence, the OGL version on Nomis, whether ad hoc 006998 is APS, the ESCO to O*NET-SOC crosswalk licence, NCS salary geography.
- The in-app ILO label text (frontend) still paraphrases the disclaimer; the data and docs carry the exact wording.
