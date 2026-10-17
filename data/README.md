# data/

- `manifest.yaml`: every raw input, where it comes from, how to get it, licence. Start here.
- `raw/`: downloads. **Gitignored.** Fetch with `make data` (scripted sources) plus the browser
  downloads listed in the manifest, then `make data-sync` to copy to the cluster.
- `curated/`: hand-made, committed, every row `verified_by`.
- `manifest.lock.json`: checksums written by `make data-check`; commit it.

Small derived artefacts the app loads (`careers.json`, `backtest.json`, ...) go in `/snapshots/`.
