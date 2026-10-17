# Codex: integration harness

- **Owner:** Yehor / Codex
- **Branch:** `codex/integration-harness`
- **PR:** #7 (draft): https://github.com/yehorm14/Avenir/pull/7
- **Status:** ready for review

## Task
Build and test an isolated integration harness for team branches and ML v1.1.
Report cross-slice breakages without modifying the owning slices.

## Done so far
- Added stdlib merge orchestration, safe detached-worktree cleanup, conflict recovery,
  automatic Arsenii branch discovery, optional ML replacement, pytest/lint summaries,
  owner triage, baseline/overlay/freeze comparison and automatic shared status updates.
- Added an ML probe checking import isolation, all occupation metrics' flags, demo
  loader flags/counts, vocabulary compatibility and snapshot sizes.
- Added tests using local temporary Git repositories, plus real pytest/ruff subprocesses.
- Validation: 22 harness tests and 32 existing checkout tests passed; lint clean.
  `make check SHELL=C:/Progra~1/Git/bin/bash.exe` exited 0 using portable tools in
  the shared tooling directory; its historical scanner caveat is recorded below.
- Documented usage and report limitations in `scripts/integration/README.md`.
- Initial report: `integration-report-2151.md` in the shared handoff directory.
  Baseline 95 passed; overlay and freeze each 103 passed, 1 failed; lint clean.
- Contract v1.1 report: `integration-report-2154.md`. Four branches merged, no conflicts;
  live-adapters unavailable at fetch. Baseline 101 passed; overlay and freeze each
  109 passed, 1 failed; lint clean. Unknown metric keys resolved by contract v1.1.
- Final harness/report-status verification: `integration-report-2158.md`, same
  results as 21:54; first history year 2007 confirmed by the probe; cleanup successful.
- Latest report with live-adapters: `integration-report-2159.md`. All five available
  default branches merged with no conflicts. Baseline 276 passed; ML v1.1 overlay
  and freeze each 287 passed, 1 failed; lint clean. Adapter and ETL tests pass.
- Latest requested expanded run: `integration-report-2202.md`, including
  frontend-handoff and contract fix `0ed4785`. All six branches merge cleanly.
  Baseline 287 passed, 1 failed; overlay/freeze each 299 passed, 1 failed; lint clean.
  The history test now passes. The remaining failing ID is
  `packages/contracts/tests/test_examples.py::test_committed_pack_is_not_stale`
  in all three modes; no failure is unique to v1.1. The runtime ML probe still passes.
- Both probes read 412 ML occupations, expose 20 demo careers through `load_data()`,
  preserve all 5,768 joined metric flags and all 280 loaded demo metric flags.
  No JSON file exceeds 5 MB. These counts are observations from overlay `03fb482`.
- Scheduled single checkpoints in this chat for 17 Oct 23:30, 18 Oct 01:00 and
  18 Oct 08:30 Europe/London, plus a quiet 15-minute branch/handoff watcher until freeze.

## Blocked on
- No harness implementation blocker.
- Yehor owns the stale frontend handoff pack test. The handoff was generated from
  main and its status notes regeneration after contract v1.1; generated examples
  also depend on selected ML evidence. Report the mismatch; do not regenerate or
  modify files in that slice. The earlier history-start failure is fixed in `0ed4785`.
- No Arsenii branch was available in the latest recorded run; the overlay is still
  needed for v1.1. Live-adapters and contract-v1.1 were both included successfully.
- Repository-wide gitleaks reports two pre-existing `generic-api-key` findings in
  historical `prototypes/pathfinder-game/frontend/src/screens/Advisers.tsx`, lines 11
  and 22, commit `e928ad8151afb914f4842f91777008e1397c787c`. No finding values were
  printed or copied. The current harness file scan is clean; historical findings
  need human triage outside this lane. The Makefile masks the scanner exit status.

## Open questions (for humans)
- The strict integration lane excludes the root README. Usage and Codex disclosure
  are recorded here and in the integration README; the glue owner can update the
  root README's AI disclosure.
- The harness is development tooling and necessarily reads Git/files and launches
  checks. AGENTS rule 5 is interpreted as applying to application data access.
- Confirm the historical scanner findings; this work does not classify them as
  actual credentials or alter repository history.

## Marked (verify)
- None. Missing branches and execution limitations are reported explicitly.

## Next step
Review the draft harness PR and the newest report in the shared handoff directory.
Use `C:/dev/Avenir/.venv/Scripts/python.exe` from `C:/dev/Avenir-wt/codex-harness`.
Run `python -m pytest scripts/integration -q` explicitly: root pytest's configured
test paths do not include this development tooling. Run the harness with
`--overlay-ml 03fb482` until Arsenii branches appear, then run without the overlay.
Claude requested frontend-handoff in addition to the five script defaults. Fetch
refs first, then use `--branches` containing those five, every `origin/arsenii/*`
ref, and `origin/yehor/frontend-handoff`. Keep the source defaults unchanged.
Read `claude-status.md` before each step. Never edit another slice or send messages.
