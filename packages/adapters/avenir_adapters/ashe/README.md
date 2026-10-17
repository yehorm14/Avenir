# adapter: ashe

The only code allowed to read this source. Returns Metric objects with full provenance
(see `docs/contracts.md`). Ships a small fixture in `snapshots/` for tests and the demo.
Static: reads `data/raw/` or `data/curated/` during ETL; the app reads the derived snapshot.
Source details: `data/manifest.yaml`.
