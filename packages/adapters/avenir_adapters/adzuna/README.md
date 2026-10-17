# adapter: adzuna

The only code allowed to read this source. Returns Metric objects with full provenance
(see `docs/contracts.md`). Ships a small fixture in `snapshots/` for tests and the demo.
Live: 3 s timeout, 1 retry, then the latest `snapshots/adzuna/*.json` with status "snapshot".
Source details: `data/manifest.yaml`.
