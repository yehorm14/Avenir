# Avenir app API

This small API joins Arsenii's actual committed ML artefacts with Max's original
Pathfinder pathway planner. No credentials, external requests, generated salary
figures or replacements for the committed evidence are needed.

From the repository root, with Python 3.12 or newer:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r apps/web/api/requirements.txt
cd apps/web
../../.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8015
```

The frontend Vite proxy uses port 8015. CORS permits localhost and 127.0.0.1 on
ports 4175 and 5173. All data paths resolve relative to the module, so the same
command also works after cloning the entire repository to another directory.

Tests, from the repository root:

```sh
.venv/bin/python -m pytest apps/web/api/tests -q
```

## Endpoints

- `GET /api/health`: status, career count, ML mode, guide mode.
- `GET /api/bootstrap`: `careers`, `tags`, `sources` (registry), `backtest`
  (original full artefact), `crises` (array), `data_status`.
- `POST /api/matches`: `{ "tags": ["computers_coding"], "weights":
  { "pay": 30, "interest": 50, "need": 20 } }` returns all sorted careers
  as `results`, a `method` explanation and `fit_status`.
- `GET /api/path/2134?nation=Scotland`: Max's original PathPlan JSON with
  `pathway_status: "curated_demo"`. Degrees have `median_earnings_15m: null`:
  Max's illustrative course earnings never replace Arsenii's career evidence.
- `POST /api/guide`: `{ "soc": "2134", "message": "What skills can I build?",
  "history": [] }` returns `text`, `mode: "prepared_demo"`, `ai_written: false`,
  `sources` and an explicit note. History items use `{role, content}`. Replies
  use prepared templates and exact supplied numbers; no live LLM is connected.

Every career has `soc`, `title`, `summary`, `sector`, `family`, `skills`,
`metrics`, `history`, and `hedges`. Quantitative metrics, history and hedge
candidates pass through `pathfinder_ml.ML` without changing values or flags.
A match adds `score`, `fit`, `pay_score`, `need_score`, `reasons`, `fit_status`.

Pay and need are percentile ranks of available medians and observed 2021–2025
job trends. Fit is the mean of Arsenii's supplied tag affinities. All scores run
0–100, with ties sorted by SOC. Missing evidence stays null and is excluded
from the weighted mean; all-zero weights become equal weights. If all inputs
with positive weight are missing, the overall score is also null. Need is a
historical signal, not an LLM prediction. Matching and hedge statuses come from the supplied artefacts. At source commit
`cb9e169ce417fa35d276826073a1d6ba67815d46`, both are `preliminary`: fit
affinities were produced by BGE-base embeddings and evaluated on a synthetic
development set, with held-out human evaluation still pending. The bootstrap
includes the original fit method/evaluation and each artefact's real/mock origin.
Unknown tags return HTTP 422.

Some of Arsenii's 20 career codes were absent from Max's earlier prototype.
The text-only mapping in `TEXT_BRIDGES` reuses a related family pathway and
adds `related_pathway_soc` plus a visible explanation in `demo_note`. Numeric
data always comes from the requested Arsenii SOC. University and competition
content remains curated demo material, not a university ranking or a live
calendar; the original caution is preserved on every path.

The ML slice is imported unchanged from Arsenii's KATYATA commit
`cb9e169ce417fa35d276826073a1d6ba67815d46` (`packages/ml` and `snapshots/ml`
only). It contains evidence for 412 occupations; this app displays the same
20-career demo set. Histories span 2007–2025, with no job counts before 2011.
