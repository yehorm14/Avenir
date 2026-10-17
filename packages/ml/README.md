# packages/ml (ML and training, owner: Arsenii)

Work packages from spec section 5, in priority order:
M5 backtest -> `snapshots/backtest.json`; M4 demand trend -> `demand.json`;
M3 hedge similarity -> `hedge.json`; M1 interest matcher -> model + `matcher_eval.json`;
M2 in-house exposure -> `exposure.json`; M6 evaluation set.
Big model files go in `packages/ml/models/` (gitignored). Backtest rule: features for year Y read
only data published for Y or earlier, with a test proving it.
