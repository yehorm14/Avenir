"""Hedge-career candidates from shared ESCO skills (baseline, rule fixed before looking at results).

Usage: python -I hedges_build.py RAW_DIR PROCESSED_DIR

For each SOC 2020 group, a skill vector is built from its linked ESCO occupations
(soc2020_esco_links.csv): weight = link weight x (1.0 essential, 0.5 optional) x IDF,
where IDF = log(N / number of SOC groups that have the skill), so near-universal
skills (teamwork, communication) count for little. Similarity between two groups is
weighted Jaccard: sum(min) / sum(max). Writes PROCESSED_DIR/hedges_candidates.json with
the top 5 per group and their most important shared skills.

v1.2 (after review): a pair's evidence is the weaker of its two sides; candidates below a
similarity of 0.05 are dropped; pairs whose skill vectors are identical because both rest only on
the same ISCO fallback (similarity 1.0) are dropped, since they are not evidence of anything.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

TOP_K = 5
MIN_SIMILARITY = 0.05
RELATION_WEIGHT = {"essential": 1.0, "optional": 0.5}


def skill_level(soc: str) -> int:
    """ONS skill level by SOC 2020 major group (sub-major 12, 'other managers', is level 3).
    Hedges must share the level, so a hedge is never a step down (agreed 17 Oct)."""
    major = soc[0]
    if major == "1":
        return 3 if soc.startswith("12") else 4
    return {"2": 4, "3": 3, "5": 3, "4": 2, "6": 2, "7": 2, "8": 2, "9": 1}[major]


def main() -> None:
    raw, proc = Path(sys.argv[1]), Path(sys.argv[2])
    links = pd.read_csv(proc / "soc2020_esco_links.csv", dtype={"soc2020": str})
    rel = pd.read_csv(raw / "esco" / "occupationSkillRelations_en.csv", dtype=str)
    skills_df = pd.read_csv(raw / "esco" / "skills_en.csv", dtype=str)
    print(f"skills_en.csv: {len(skills_df)} rows, {skills_df.conceptUri.nunique()} unique skill URIs")
    skills = skills_df.drop_duplicates("conceptUri").set_index("conceptUri")["preferredLabel"]
    rel["rw"] = rel.relationType.map(RELATION_WEIGHT).fillna(0.5)

    m = links.merge(rel, left_on="esco_uri", right_on="occupationUri")
    m["w"] = m.w_in_soc * m.rw
    tf = m.groupby(["soc2020", "skillUri"]).w.sum()
    n_groups = links.soc2020.nunique()
    df = tf.reset_index().groupby("skillUri").soc2020.nunique()
    idf = (n_groups / df).map(math.log)
    vec = defaultdict(dict)
    for (soc, skill), w in tf.items():
        vec[soc][skill] = w * idf[skill]

    quality = links.groupby("soc2020").link_type.apply(lambda s: "estimate" if (s == "isco_fallback").any() and (s != "isco_fallback").sum() < 3 else "title")
    socs = sorted(vec)
    out = {}
    for a in socs:
        va = vec[a]
        sa = sum(va.values())
        scored = []
        for b in socs:
            if a == b or skill_level(a) != skill_level(b):
                continue
            vb = vec[b]
            inter = sum(min(w, vb[s]) for s, w in va.items() if s in vb)
            if inter == 0:
                continue
            union = sa + sum(vb.values()) - inter
            scored.append((inter / union, b))
        scored.sort(reverse=True)
        ev_a = quality.get(a, "estimate")
        scored = [(sim, b) for sim, b in scored if sim >= MIN_SIMILARITY
                  and not (sim >= 0.999 and ev_a == "estimate" and quality.get(b, "estimate") == "estimate")]
        cands = []
        for sim, b in scored[:TOP_K]:
            shared = sorted(((min(w, vec[b][s]), s) for s, w in va.items() if s in vec[b]), reverse=True)
            evidence = "estimate" if "estimate" in (ev_a, quality.get(b, "estimate")) else "title"
            cands.append({"soc2020": b, "similarity": round(sim, 4), "shared_skills": [skills.get(s, s) for _, s in shared[:6]],
                          "n_shared": len(shared), "evidence": evidence})
        out[a] = {"evidence": quality.get(a, "estimate"), "candidates": cands}
    (proc / "hedges_candidates.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"skill vectors: {len(vec)} groups; distinct skills: {len(idf)}; written {len(out)} candidate lists")


if __name__ == "__main__":
    main()
