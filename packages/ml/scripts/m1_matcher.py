"""M1: the interest matcher. Builds career texts, evaluates matching methods on labelled profiles,
and writes fit.json from the winning method.

Usage:
  python -I m1_matcher.py texts  RAW_DIR PROCESSED_DIR
  python -I m1_matcher.py eval   PROCESSED_DIR SNAPSHOT_DIR --labels CSV [CSV ...] --split dev|test|all [--out JSON]
  python -I m1_matcher.py build-fit PROCESSED_DIR SNAPSHOT_DIR --method embed_tags|bm25_tags --eval JSON

Methods (fixed before looking at results):
  random        expected top-3 hit rate by chance, given how many careers each row labels
  keyword_tags  the runtime chain with the hand-made affinity table (ml_common.AFFINITY, frozen baseline)
  bm25          lexical retrieval: profile text against each career's text (title, ESCO labels,
                descriptions, distinctive skills); a proper keyword baseline
  embed         BGE-base embeddings; score = max cosine over the career's ESCO text chunks
  embed_tags    the runtime chain with an embedding-derived affinity table (tag -> career);
                this is what fit.json ships, because the app runtime is standard-library only

Metrics: hit@1, hit@3 (any labelled career in the top 3), MRR, with seeded bootstrap 95% CIs.
Splits: rows from files whose name contains "synthetic" are development only; team label rows
are split by a hash of profile_id (40% dev, 60% test). The test split is scored once, at the end.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml_common import AFFINITY, DEMO, NOW, SCHEMA_VERSION, TAGS  # noqa: E402

EMBED_MODEL = "BAAI/bge-base-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
RNG = np.random.default_rng(0)
TOP_K = 3


# ----------------------------------------------------------------------------- texts
def build_texts(raw: Path, proc: Path) -> dict:
    occ = pd.read_csv(raw / "esco" / "occupations_en.csv", dtype=str).drop_duplicates("conceptUri").set_index("conceptUri")
    links = pd.read_csv(proc / "soc2020_esco_links.csv", dtype={"soc2020": str})
    rel = pd.read_csv(raw / "esco" / "occupationSkillRelations_en.csv", dtype=str)
    skills = pd.read_csv(raw / "esco" / "skills_en.csv", dtype=str).drop_duplicates("conceptUri").set_index("conceptUri")["preferredLabel"]
    a = pd.read_parquet(proc / "ashe_long.parquet")
    titles = a[a.soc_version == 2020].drop_duplicates("soc_code").set_index("soc_code")["title"]
    ess = rel[rel.relationType == "essential"]
    n_occ = ess.occupationUri.nunique()
    df_skill = ess.groupby("skillUri").occupationUri.nunique()
    idf = (n_occ / df_skill).map(math.log)
    out = {}
    for soc in sorted(set(links.soc2020)):
        rows = links[links.soc2020 == soc]
        titled = rows[rows.link_type != "isco_fallback"]
        use = titled if len(titled) >= 3 else rows
        chunks, skill_scores = [], Counter()
        for r in use.itertuples():
            if r.esco_uri not in occ.index:
                continue
            o = occ.loc[r.esco_uri]
            desc = o["description"] if isinstance(o["description"], str) else (o["definition"] if isinstance(o["definition"], str) else "")
            chunks.append({"label": o["preferredLabel"], "text": f"{o['preferredLabel']}. {desc}".strip()})
            for s in ess[ess.occupationUri == r.esco_uri].skillUri:
                skill_scores[s] += r.w_in_soc * idf.get(s, 0.0)
        top_skills = [skills.get(s, s) for s, _ in skill_scores.most_common(15)]
        out[soc] = {"soc2020": soc, "title": titles.get(soc, soc), "short_title": DEMO.get(soc, titles.get(soc, soc)),
                    "chunks": chunks[:12], "skills": top_skills, "evidence": "title" if len(titled) >= 3 else "estimate"}
    (proc / "career_texts.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"career texts for {len(out)} occupations; demo set covered: {sum(s in out for s in DEMO)} of {len(DEMO)}")
    return out


# ----------------------------------------------------------------------------- labels and splits
def load_labels(paths: list[str], split: str) -> pd.DataFrame:
    frames = []
    for p in paths:
        df = pd.read_csv(p, dtype=str).fillna("")
        df = df[~df.profile_id.str.startswith("example")]
        df["file"] = Path(p).name
        df["synthetic"] = "synthetic" in Path(p).name.lower()
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    bucket = df.profile_id.map(lambda s: int(hashlib.sha1(s.encode()).hexdigest(), 16) % 10)
    df["split"] = np.where(df.synthetic, "dev", np.where(bucket < 4, "dev", "test"))
    df["labels"] = df.apply(lambda r: [c for c in (r.best_soc_1, r.best_soc_2, r.best_soc_3) if re.fullmatch(r"\d{4}", str(c))], axis=1)
    df = df[df.labels.map(len) > 0]
    if split != "all":
        df = df[df.split == split]
    return df.reset_index(drop=True)


# ----------------------------------------------------------------------------- methods
def tokens(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for t in toks:
        if len(t) > 4:
            for suf in ("ing", "ed", "es", "s"):
                if t.endswith(suf) and len(t) - len(suf) >= 4:
                    t = t[: -len(suf)]
                    break
        out.append(t)
    return out


class BM25:
    def __init__(self, docs: dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.ids = list(docs)
        self.tf = [Counter(tokens(docs[i])) for i in self.ids]
        self.len = np.array([sum(c.values()) for c in self.tf], float)
        self.avg = self.len.mean()
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(self.ids)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> dict[str, float]:
        q = tokens(query)
        out = {}
        for i, (doc_id, c) in enumerate(zip(self.ids, self.tf)):
            s = 0.0
            for t in q:
                if t in c:
                    f = c[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            out[doc_id] = s
        return out


def career_doc(entry: dict) -> str:
    return " ".join([entry["title"], entry["short_title"]] + [c["text"] for c in entry["chunks"]] + entry["skills"])


class Embedder:
    def __init__(self, model_path: str | None = None):
        import torch
        from sentence_transformers import SentenceTransformer
        self.name = model_path or EMBED_MODEL
        self.model = SentenceTransformer(self.name, device="cuda" if torch.cuda.is_available() else "cpu")

    def encode(self, texts: list[str], query: bool = False) -> np.ndarray:
        if query:
            texts = [QUERY_PREFIX + t for t in texts]
        return np.asarray(self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False))


def embed_career_chunks(embedder: Embedder, texts: dict) -> dict[str, np.ndarray]:
    out = {}
    for soc, e in texts.items():
        chunk_texts = [c["text"] for c in e["chunks"]] or [e["title"]]
        chunk_texts.append(f"{e['title']}. Skills: {', '.join(e['skills'])}")
        out[soc] = embedder.encode(chunk_texts)
    return out


def embed_scores(q: np.ndarray, career_vecs: dict[str, np.ndarray]) -> dict[str, float]:
    return {soc: float((v @ q).max()) for soc, v in career_vecs.items()}


def tag_affinity_from_embeddings(embedder: Embedder, career_vecs: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    """tag -> career -> 0..1. Cosine of the tag description against each career's chunks (max),
    then min-max scaled within the tag so the best career for a tag is 1 and the worst 0."""
    aff = {}
    for tag_id, label, kws in TAGS:
        q = embedder.encode([f"{label}: {', '.join(k.rstrip('*') for k in kws)}"], query=True)[0]
        raw = embed_scores(q, career_vecs)
        lo, hi = min(raw.values()), max(raw.values())
        aff[tag_id] = {soc: round((s - lo) / (hi - lo), 4) if hi > lo else 0.0 for soc, s in raw.items()}
    return aff


def chain_scores(ml, text: str, affinity: dict) -> dict[str, float]:
    tags = [t["tag"] for t in ml.match_tags(text, top_k=5)]
    if not tags:
        return {}
    socs = set().union(*[set(affinity[t]) for t in tags if t in affinity])
    return {soc: sum(affinity[t].get(soc, 0.0) for t in tags) / len(tags) for soc in socs}


# ----------------------------------------------------------------------------- metrics
def rank_of_best(scores: dict[str, float], labels: list[str], universe: list[str]) -> int | None:
    order = sorted(universe, key=lambda s: (-scores.get(s, 0.0), s))
    positions = [order.index(l) + 1 for l in labels if l in order]
    return min(positions) if positions else None


def summarise(ranks: list, n_labels: list[int], universe_size: int) -> dict:
    hit1 = np.array([r == 1 for r in ranks], float)
    hit3 = np.array([r is not None and r <= TOP_K for r in ranks], float)
    mrr = np.array([1.0 / r if r else 0.0 for r in ranks])

    def ci(x):
        draws = RNG.choice(x, size=(2000, len(x)), replace=True).mean(axis=1)
        return [round(float(np.percentile(draws, 2.5)), 3), round(float(np.percentile(draws, 97.5)), 3)]
    chance = float(np.mean([1 - math.comb(universe_size - k, TOP_K) / math.comb(universe_size, TOP_K) for k in n_labels]))
    return {"n": len(ranks), "hit_at_1": round(float(hit1.mean()), 3), "hit_at_3": round(float(hit3.mean()), 3), "hit_at_3_ci95": ci(hit3),
            "mrr": round(float(mrr.mean()), 3), "chance_hit_at_3": round(chance, 3)}


def paired_delta(ranks_a: list, ranks_b: list) -> dict:
    a = np.array([r is not None and r <= TOP_K for r in ranks_a], float)
    b = np.array([r is not None and r <= TOP_K for r in ranks_b], float)
    d = a - b
    draws = RNG.choice(d, size=(2000, len(d)), replace=True).mean(axis=1)
    return {"delta_hit_at_3": round(float(d.mean()), 3), "ci95": [round(float(np.percentile(draws, 2.5)), 3), round(float(np.percentile(draws, 97.5)), 3)]}


# ----------------------------------------------------------------------------- commands
def cmd_eval(args) -> dict:
    proc, snap = Path(args.processed), Path(args.snapshot)
    texts = json.loads((proc / "career_texts.json").read_text(encoding="utf-8"))
    universe = [s for s in DEMO if s in texts]
    texts = {s: texts[s] for s in universe}
    df = load_labels(args.labels, args.split)
    if df.empty:
        raise SystemExit(f"no labelled rows for split '{args.split}'")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from pathfinder_ml import ML
    # The chain always tags text with the current keyword list (ml_common.TAGS), and the keyword
    # baseline is frozen to the hand-made table (ml_common.AFFINITY), so it never silently becomes
    # whatever fit.json was last built with.
    import tempfile
    tag_dir = Path(tempfile.mkdtemp(prefix="m1_tags_"))
    (tag_dir / "fit.json").write_text(json.dumps({"schema_version": SCHEMA_VERSION, "status": "mock", "generated_at": NOW, "method": "eval tags",
                                                  "tags": [{"id": t, "label": lbl, "keywords": kws} for t, lbl, kws in TAGS],
                                                  "affinity": AFFINITY}), encoding="utf-8")
    ml = ML(data_dir=tag_dir, mock_dir=snap)
    shipped_aff = AFFINITY
    bm25 = BM25({s: career_doc(e) for s, e in texts.items()})
    embedder = Embedder()
    career_vecs = embed_career_chunks(embedder, texts)
    emb_aff = tag_affinity_from_embeddings(embedder, career_vecs)
    qvecs = embedder.encode(df.profile_text.tolist(), query=True)
    methods = ["keyword_tags", "bm25", "embed", "embed_tags"]
    ft = None
    if args.model:
        ft = Embedder(args.model)
        ft_vecs = embed_career_chunks(ft, texts)
        ft_aff = tag_affinity_from_embeddings(ft, ft_vecs)
        ft_q = ft.encode(df.profile_text.tolist(), query=True)
        methods += ["embed_ft", "embed_ft_tags"]

    ranks = {m: [] for m in methods}
    rows = []
    for i, r in df.iterrows():
        per = {"keyword_tags": chain_scores(ml, r.profile_text, shipped_aff), "bm25": bm25.scores(r.profile_text),
               "embed": embed_scores(qvecs[i], career_vecs), "embed_tags": chain_scores(ml, r.profile_text, emb_aff)}
        if ft is not None:
            per["embed_ft"] = embed_scores(ft_q[i], ft_vecs)
            per["embed_ft_tags"] = chain_scores(ml, r.profile_text, ft_aff)
        row = {"profile_id": r.profile_id, "split": r.split, "labels": r.labels}
        for m, sc in per.items():
            rk = rank_of_best(sc, r.labels, universe)
            ranks[m].append(rk)
            row[m] = {"rank_of_best_label": rk, "top3": sorted(universe, key=lambda s: (-sc.get(s, 0.0), s))[:TOP_K]}
        rows.append(row)
    n_labels = df.labels.map(len).tolist()
    result = {"split": args.split, "files": sorted(set(df.file)), "universe_size": len(universe), "generated_at": NOW,
              "base_model": EMBED_MODEL, "fine_tuned_model": args.model,
              "methods": {m: summarise(rk, n_labels, len(universe)) for m, rk in ranks.items()},
              "paired_vs_bm25": {m: paired_delta(ranks[m], ranks["bm25"]) for m in methods if m != "bm25"},
              "paired_vs_embed": {m: paired_delta(ranks[m], ranks["embed"]) for m in methods if m.startswith("embed_ft")},
              "rows": rows}
    print(f"split={args.split} n={len(df)} universe={len(universe)} chance hit@3={result['methods']['bm25']['chance_hit_at_3']}")
    for m, s in result["methods"].items():
        print(f"  {m:13s} hit@1 {s['hit_at_1']:.2f}  hit@3 {s['hit_at_3']:.2f} {s['hit_at_3_ci95']}  mrr {s['mrr']:.2f}")
    for m, d in result["paired_vs_bm25"].items():
        print(f"  {m:13s} vs bm25: delta hit@3 {d['delta_hit_at_3']:+.2f} {d['ci95']}")
    for m, d in result["paired_vs_embed"].items():
        print(f"  {m:13s} vs embed: delta hit@3 {d['delta_hit_at_3']:+.2f} {d['ci95']}")
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
        print("written", args.out)
    return result


def cmd_build_fit(args) -> None:
    proc, snap = Path(args.processed), Path(args.snapshot)
    texts = json.loads((proc / "career_texts.json").read_text(encoding="utf-8"))
    universe = [s for s in DEMO if s in texts]
    texts = {s: texts[s] for s in universe}
    ev = json.loads(Path(args.eval).read_text(encoding="utf-8"))
    if args.method == "embed_tags":
        embedder = Embedder()
        aff = tag_affinity_from_embeddings(embedder, embed_career_chunks(embedder, texts))
        method = (f"Tag-to-career affinities from {EMBED_MODEL} cosine similarity (max over ESCO text chunks), min-max scaled per tag; "
                  "runtime maps free text to tags by keyword and averages affinities.")
    else:
        bm25 = BM25({s: career_doc(e) for s, e in texts.items()})
        aff = {}
        for tag_id, label, kws in TAGS:
            raw = bm25.scores(f"{label} {' '.join(k.rstrip('*') for k in kws)}")
            lo, hi = min(raw.values()), max(raw.values())
            aff[tag_id] = {s: round((v - lo) / (hi - lo), 4) if hi > lo else 0.0 for s, v in raw.items()}
        method = "Tag-to-career affinities from BM25 over career texts, min-max scaled per tag; runtime maps free text to tags by keyword."
    status = "final" if ev.get("split") == "test" else "preliminary"
    payload = {"schema_version": SCHEMA_VERSION, "status": status, "generated_at": NOW, "method": method,
               "evaluation": {"split": ev["split"], "n": ev["methods"]["bm25"]["n"], "universe_size": ev["universe_size"],
                              "note": ("Matcher scores were checked on a development split of synthetic profiles only. No real "
                                       "learner labels have been scored yet, so the matcher is preliminary." if ev["split"] != "test" else "Scored once on the held-out team labels."),
                              "methods": ev["methods"], "paired_vs_bm25": ev["paired_vs_bm25"], "paired_vs_embed": ev.get("paired_vs_embed", {})},
               "tags": [{"id": t, "label": lbl, "keywords": kws} for t, lbl, kws in TAGS], "affinity": aff}
    # The matcher service needs the career texts (ESCO-derived, open licence); ship the demo subset.
    (snap / "career_texts.json").write_text(json.dumps(texts, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for folder in (snap, snap / "mock"):
        (folder / "fit.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        ep = folder / "eval.json"
        e = json.loads(ep.read_text(encoding="utf-8"))
        e["checks"]["matcher"] = {"status": status, "date": NOW[:10],
                                  "summary": f"Matcher methods on the {ev['split']} split (n={ev['methods']['bm25']['n']}, {len(universe)} careers, chance hit@3 "
                                             f"{ev['methods']['bm25']['chance_hit_at_3']}). Shipped: {args.method}.",
                                  "metrics": {"methods": ev["methods"], "paired_vs_bm25": ev["paired_vs_bm25"]}}
        ep.write_text(json.dumps(e, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"fit.json written ({args.method}, status {status}) to {snap} and {snap / 'mock'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("texts"); t.add_argument("raw"); t.add_argument("processed")
    e = sub.add_parser("eval"); e.add_argument("processed"); e.add_argument("snapshot"); e.add_argument("--labels", nargs="+", required=True)
    e.add_argument("--split", default="dev", choices=["dev", "test", "all"]); e.add_argument("--out"); e.add_argument("--model", help="path to a fine-tuned model to compare")
    b = sub.add_parser("build-fit"); b.add_argument("processed"); b.add_argument("snapshot"); b.add_argument("--method", required=True, choices=["embed_tags", "bm25_tags"])
    b.add_argument("--eval", required=True)
    args = ap.parse_args()
    if args.cmd == "texts":
        build_texts(Path(args.raw), Path(args.processed))
    elif args.cmd == "eval":
        cmd_eval(args)
    else:
        cmd_build_fit(args)


if __name__ == "__main__":
    main()
