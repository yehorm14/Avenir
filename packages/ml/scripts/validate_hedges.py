"""Reference check of hedge candidates against O*NET's related occupations (US).

Usage: python -I validate_hedges.py RAW_DIR PROCESSED_DIR

Path: UK SOC 2020 -> linked ESCO occupations (soc2020_esco_links.csv) -> O*NET-SOC
(O*NET's ESCO crosswalk) -> O*NET related occupations (Primary tiers) -> back to UK SOC.
R(A) is the set of UK groups O*NET considers related to group A.

Metric fixed in advance: hit rate = share of our top-3 hedges that fall in R(A).
Baselines: (1) 3 random groups at the same skill level (expected rate computed
exactly); (2) groups in the same 3-digit SOC minor group. This is a reference
check, not a training signal: nothing is tuned to it.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from hedges_build import skill_level  # noqa: E402


def norm(text: str) -> str:
    text = str(text).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    raw, proc = Path(sys.argv[1]), Path(sys.argv[2])
    cw = pd.read_excel(raw / "onet" / "ESCO_to_ONET-SOC.xlsx", header=3, dtype=str)
    cw.columns = ["esco_code", "esco_title", "onet", "onet_title"]
    cw = cw.dropna(subset=["esco_title", "onet"])
    occ = pd.read_csv(raw / "esco" / "occupations_en.csv", dtype=str)
    occ["key"] = occ.preferredLabel.map(norm)
    cw["key"] = cw.esco_title.map(norm)
    esco_onet = cw.merge(occ[["conceptUri", "key"]], on="key")[["conceptUri", "onet"]].drop_duplicates()
    print(f"crosswalk rows: {len(cw)}; matched to ESCO occupations: {esco_onet.conceptUri.nunique()} of {len(occ)}")

    links = pd.read_csv(proc / "soc2020_esco_links.csv", dtype={"soc2020": str})
    links = links[links.link_type != "isco_fallback"]
    soc_onet = links.merge(esco_onet, left_on="esco_uri", right_on="conceptUri")[["soc2020", "onet"]].drop_duplicates()
    onet_soc = soc_onet.groupby("onet").soc2020.apply(set).to_dict()
    soc_codes = soc_onet.groupby("soc2020").onet.apply(set).to_dict()

    rel = pd.read_csv(raw / "onet" / "related_occupations.csv", dtype=str)
    rel = rel[rel["Relatedness Tier"].str.startswith("Primary")]
    related = rel.groupby("O*NET-SOC Code")["Related O*NET-SOC Code"].apply(set).to_dict()

    R = defaultdict(set)
    for soc, codes in soc_codes.items():
        for c in codes:
            for rc in related.get(c, ()):
                R[soc] |= onet_soc.get(rc, set())
        R[soc].discard(soc)

    hedges = json.loads((proc / "hedges_candidates.json").read_text(encoding="utf-8"))
    all_socs = sorted(hedges)
    rows = []
    for soc, entry in hedges.items():
        if soc not in R or not R[soc] or entry["evidence"] != "title":
            continue
        top = [c["soc2020"] for c in entry["candidates"][:3]]
        if not top:
            continue
        hit = sum(t in R[soc] for t in top) / len(top)
        same_level = [s for s in all_socs if s != soc and skill_level(s) == skill_level(soc)]
        rand = len([s for s in same_level if s in R[soc]]) / len(same_level)
        minor = [s for s in same_level if s[:3] == soc[:3]]
        minor_rate = (len([s for s in minor if s in R[soc]]) / len(minor)) if minor else None
        rows.append((soc, hit, rand, minor_rate, len(R[soc])))
    df = pd.DataFrame(rows, columns=["soc2020", "hit_at_3", "random_same_level", "same_minor_group", "n_related"])
    print(f"groups checked (title evidence, with O*NET links): {len(df)}")
    print(f"hit rate @3, our hedges: {df.hit_at_3.mean():.1%}")
    print(f"baseline, 3 random same-level groups: {df.random_same_level.mean():.1%}")
    print(f"baseline, same 3-digit group: {df.same_minor_group.dropna().mean():.1%} (over {df.same_minor_group.notna().sum()} groups with siblings)")
    df.to_csv(proc / "hedge_validation.csv", index=False)
    demo = ["2134", "3544", "2133", "2135", "2141", "2142", "2451", "2452", "3120", "2121", "2123", "3113", "2453", "2454", "2433", "2422", "2421", "2254", "5241", "2313"]
    d = df[df.soc2020.isin(demo)]
    print(f"demo careers checked: {len(d)} of 20; their hit rate @3: {d.hit_at_3.mean():.1%}")
    print(d.sort_values("hit_at_3").to_string(index=False))


if __name__ == "__main__":
    main()
