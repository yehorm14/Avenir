# Codex: My plan and Jobs sources cleanup

- **Owner:** Codex
- **Branch:** `codex/final-delivery`
- **PR:** none
- **Status:** done and pushed

## Task
Remove the annotated My plan status row and make the long Jobs Sources section collapsible without dropping references or attribution.

## Done so far
- Removed the `Explore first / Change career` row and its unused callback/styles.
- Converted the entire Jobs sources and attribution section into a native disclosure, closed initially.
- Updated the app documentation and decision record.
- Latest `git fetch origin` failed because github.com could not be resolved; checkout started clean and aligned with its tracking ref.
- Full `make check`: 716 passed, 3 optional skipped; Ruff/Prettier/build/secret scan passed.
- Isolated Chrome checked both pages; Sources begins closed and reveals all 12 links when opened. At 390px no horizontal overflow or console messages appeared.

## Blocked on
- None.

## Open questions (for humans)
- None.

## Marked (verify)
- None.

## Next step
No further action. Published commit: `c4297f4` on `origin/codex/final-delivery`.
