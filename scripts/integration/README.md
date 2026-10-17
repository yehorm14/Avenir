# Integration harness

Run from the harness checkout using the project's Python environment:

```powershell
& C:/dev/Avenir/.venv/Scripts/python.exe scripts/integration/merge_all.py
& C:/dev/Avenir/.venv/Scripts/python.exe scripts/integration/merge_all.py --overlay-ml 03fb482
& C:/dev/Avenir/.venv/Scripts/python.exe scripts/integration/merge_all.py --branches origin/nazar/decision,origin/nazar/api --report-dir C:/dev/Avenir-wt/_shared
& C:/dev/Avenir/.venv/Scripts/python.exe -m pytest scripts/integration -q
```

The script fetches Avenir refs, creates a detached tree from `origin/main`, then
merges decision, API, catalogue, live adapters, contract v1.1, and every available
`origin/arsenii/*` ref in that order. `--branches` replaces that entire list.
Missing refs are reported and skipped. Each conflicting merge is aborted before
trying the next ref; later checks therefore exclude that branch's changes.

With `--overlay-ml`, baseline tests run first. The script then replaces only
`packages/ml` and `snapshots/ml` with the selected KATYATA revision, without
committing, and repeats tests and lint. It always runs tests once more with
`AVENIR_FREEZE=1`, using whichever evidence was selected. Lint is not repeated for
freeze mode because the files are identical. KATYATA refs must already be fetched.

Each run writes `integration-report-HHMM.md` in UK civil time, adding a numeric
suffix if that minute already has a report, and refreshes `codex-status.md`.
Reports contain branch SHAs, conflict
files, JUnit-derived failing test IDs, lint locations, owner groups, an ML probe,
and the changes in failing IDs between baseline, overlay and freeze modes. A
shared failing ID can have a different underlying cause; the comparison does not
claim otherwise. Full subprocess output is discarded rather than saved.

The ML probe verifies that imports come from the temporary tree, counts all ML
occupations separately from the demo careers returned by `load_data()`, checks
every occupation's metric flags through `join_career`, checks flags on the loaded
demo set, identifies unknown metric keys, and lists JSON file sizes. It reports
validation exception types and field locations without copying input values.
Snapshot sizes above 5,000,000 bytes are marked. The current team rule on snapshot
size must also be checked by the reviewer; the harness does not grant exceptions.

Check subprocesses use the tree's own packages and remove API-key, token, secret,
password and credential environment variables, snapshot-directory overrides and
pytest overrides. The primary editable install cannot silently satisfy the ML
probe: the report records whether imports resolve inside the temporary tree.
No `.env` is copied. No live source calls or data downloads are made by the harness.

Only an exact, registered, detached temporary worktree named
`codex-integration-tmp` is eligible for removal. An unrelated directory, attached
branch, locked worktree or link is refused. A lock prevents overlapping runs.
On interruption, inspect the active process before removing a stale lock; rerun
to remove a stale detached tree. The harness never pushes, edits issues, or edits
another checkout. Exit 1 indicates test/lint failures, merge conflicts/errors, or
an orchestration error; exit 2 means the harness could not start. Missing optional
branches are not themselves failures.

The test module uses tiny local repositories with pytest's `tmp_path`, including
real merges and conflicts. No test pushes to a network remote. On restricted
Windows runners, point `TEMP` and `TMP` at an approved writable temporary folder
if pytest cannot create its default temporary directory.
