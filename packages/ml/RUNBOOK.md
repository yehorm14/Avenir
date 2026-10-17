# Compute runbook for the ML slice (Arsenii)

**Status 18 Oct:** every job, including the matcher fine-tune, runs on a laptop GPU in minutes. Nothing in the demo needs a GPU server. A shared GPU machine was prepared only for an optional bulk LLM labelling job (the in-house exposure check), and that job is paused.

Machine names, storage paths, user names and key files are deliberately not written here. Keep them in your own notes, never in the repo.

## 1. What runs where

| Job | Where | Why |
| --- | --- | --- |
| ASHE, crosswalks, ILO, CPIH, backtest, demand, resilience, hedges | Laptop CPU | Small tables; the whole build takes about a minute |
| Matcher baselines (keyword, BM25, BGE-base embeddings) | Laptop, GPU optional | BGE-base is 110M parameters; CPU is fine for inference |
| Matcher fine-tune | Laptop GPU (about 2 minutes) | Benched: it did not clearly beat the base model |
| Optional in-house exposure labelling with a local LLM | A shared GPU machine, if ever needed | Paused; first in the cut order |

## 2. Rules for any shared GPU machine

- Make no external API calls from it. Fetch and check data on the laptop, then copy it up.
- Use one GPU per job (`CUDA_VISIBLE_DEVICES`), run it under `nohup` or `tmux`, and kill only your own PIDs.
- Bring every artefact back to the laptop the same session. Only the JSON in `snapshots/ml/` enters the repo; model weights and raw data never do.
- Leave no idle server holding GPUs.

## 3. Before the demo

- Cache the embedding model (`BAAI/bge-base-en-v1.5`) on the demo laptop and start the matcher service once with the network off. That proves the demo does not depend on venue wifi.
- If the service is down, the API uses the keyword tagger plus `fit.json`. That fallback is the pull-the-plug moment for the matcher.
