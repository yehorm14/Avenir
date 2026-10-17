"""Fine-tune the matcher's embedding model on synthetic (statement -> career text) pairs.

Usage: python -I m1_train.py PROCESSED_DIR STATEMENTS_JSONL OUT_DIR [--epochs 3] [--batch 32] [--lr 2e-5]

Contrastive training (in-batch negatives, the MultipleNegativesRanking objective, written as a
plain PyTorch loop so no extra packages are needed): each statement (with the BGE query prefix)
is paired with one text chunk of its career; every other career text in the batch is a negative.
Batches are built so that careers from the same 2-digit SOC group appear together, which makes
the negatives hard. Training data is synthetic only; the dev and test label files are never read.
Runs on the laptop GPU (BGE-base, 110M parameters: a few minutes). Saves the model to OUT_DIR.
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

sys.path.insert(0, str(Path(__file__).parent))
from m1_matcher import EMBED_MODEL, QUERY_PREFIX  # noqa: E402

SCALE = 20.0  # temperature used by sentence-transformers' MultipleNegativesRankingLoss


def build_pairs(texts: dict, stmts: list[dict], batch: int, rng: random.Random) -> list[tuple[str, str]]:
    by_soc: dict[str, list[str]] = {}
    for s in stmts:
        by_soc.setdefault(s["soc2020"], []).append(s["text"])
    pairs = []
    for soc, lst in by_soc.items():
        chunks = [c["text"] for c in texts[soc]["chunks"]] or [texts[soc]["title"]]
        chunks.append(f"{texts[soc]['title']}. Skills: {', '.join(texts[soc]['skills'])}")
        for t in lst:
            pairs.append((soc, QUERY_PREFIX + t, rng.choice(chunks)))
    groups: dict[str, list] = {}
    for soc, q, d in pairs:
        groups.setdefault(soc[:2], []).append((q, d))
    for g in groups.values():
        rng.shuffle(g)
    ordered = []
    keys = list(groups)
    while any(groups.values()):
        rng.shuffle(keys)
        for k in keys:
            take = groups[k][: max(2, batch // 4)]
            ordered.extend(take)
            del groups[k][: len(take)]
    return ordered


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("processed"); ap.add_argument("statements"); ap.add_argument("out")
    ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--batch", type=int, default=32); ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--max-seq", type=int, default=256)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(a.seed)

    texts = json.loads((Path(a.processed) / "career_texts.json").read_text(encoding="utf-8"))
    stmts = [json.loads(l) for l in Path(a.statements).read_text(encoding="utf-8").splitlines() if l.strip()]
    pairs = build_pairs(texts, stmts, a.batch, rng)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(EMBED_MODEL, device=device)
    model.max_seq_length = a.max_seq
    print(f"{len(pairs)} training pairs over {len({s['soc2020'] for s in stmts})} careers; device {device}")

    steps_per_epoch = (len(pairs) + a.batch - 1) // a.batch
    total = steps_per_epoch * a.epochs
    warmup = max(1, total // 10)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warmup) * max(0.0, (total - s) / max(1, total - warmup)))
    model.train()
    step, t0 = 0, time.time()
    for epoch in range(a.epochs):
        losses = []
        for i in range(0, len(pairs), a.batch):
            batch = pairs[i:i + a.batch]
            if len(batch) < 4:
                continue
            q = model.tokenize([p[0] for p in batch]); d = model.tokenize([p[1] for p in batch])
            q = {k: v.to(device) for k, v in q.items()}; d = {k: v.to(device) for k, v in d.items()}
            eq = torch.nn.functional.normalize(model(q)["sentence_embedding"], dim=-1)
            ed = torch.nn.functional.normalize(model(d)["sentence_embedding"], dim=-1)
            logits = eq @ ed.T * SCALE
            loss = torch.nn.functional.cross_entropy(logits, torch.arange(len(batch), device=device))
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
            losses.append(float(loss)); step += 1
        print(f"epoch {epoch + 1}/{a.epochs}: mean loss {sum(losses) / len(losses):.3f} ({time.time() - t0:.0f}s)")
    model.eval()
    model.save(a.out)
    (Path(a.out) / "TRAINING.json").write_text(json.dumps({"base_model": EMBED_MODEL, "pairs": len(pairs), "careers": len({s['soc2020'] for s in stmts}),
                                                            "epochs": a.epochs, "batch": a.batch, "lr": a.lr, "seed": a.seed, "max_seq": a.max_seq,
                                                            "statements_file": str(a.statements), "objective": "in-batch contrastive (MNRL), scale 20"}, indent=1))
    print("saved to", a.out)


if __name__ == "__main__":
    main()
