"""Link SOC 2020 occupations to ESCO occupations through job titles (refined rule, agreed 17 Oct).

Usage: python -I esco_link.py RAW_DIR PROCESSED_DIR

UK job titles come from the ONS SOC 2020 coding index (~32,000 titles, each with a
SOC 2020 and an ISCO-08 code). ESCO occupations have an ISCO code plus preferred
and alternative labels. The rule, fixed before looking at any hedges:

1. An exact match to an ESCO *preferred* label links across ISCO codes (ONS and
   ESCO often file the same job under different ISCO codes; a full title is
   strong evidence).
2. An exact match to an ESCO *alternative* label links only within the same ISCO
   code, and a link supported by a single alternative-label match is dropped.
3. SOC groups left with fewer than 3 links get every ESCO occupation under their
   main ISCO code as a fallback, marked link_type "isco_fallback" (shown as an
   estimate downstream).

Writes PROCESSED_DIR/soc2020_esco_links.csv:
soc2020, esco_uri, esco_label, link_type, matches, w_in_soc
"""
import re
import sys
from pathlib import Path

import pandas as pd

MIN_LINKS = 3


def norm(text: str) -> str:
    text = str(text).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    raw, proc = Path(sys.argv[1]), Path(sys.argv[2])
    idx = pd.read_excel(raw / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index", dtype=str,
                        usecols=["SOC_2020", "ISCO-08 code based on SOC2020", "INDEXOCC_-_natural_word_order"])
    idx.columns = ["soc2020", "isco08", "title"]
    idx = idx.dropna()
    idx = idx[idx.soc2020.str.fullmatch(r"\d{4}") & idx.isco08.str.fullmatch(r"\d{4}")]
    idx["key"] = idx.title.map(norm)

    occ = pd.read_csv(raw / "esco" / "occupations_en.csv", dtype=str)
    occ["isco08"] = occ["iscoGroup"].str[:4]
    pref = occ.assign(key=occ.preferredLabel.map(norm))[["conceptUri", "preferredLabel", "isco08", "key"]]
    alt_rows = []
    for r in occ.itertuples():
        if isinstance(r.altLabels, str):
            for n in r.altLabels.split("\n"):
                if n.strip() and norm(n) != norm(r.preferredLabel):
                    alt_rows.append((r.conceptUri, r.preferredLabel, r.isco08, norm(n)))
    alt = pd.DataFrame(alt_rows, columns=["conceptUri", "preferredLabel", "isco08", "key"]).drop_duplicates()

    # Rule 1: preferred labels, any ISCO code.
    m1 = idx.merge(pref, on="key", suffixes=("", "_esco"))
    p = m1.groupby(["soc2020", "conceptUri", "preferredLabel"]).size().rename("pref_matches")
    # Rule 2: alternative labels, same ISCO code only.
    m2 = idx.merge(alt, on=["key", "isco08"])
    a = m2.groupby(["soc2020", "conceptUri", "preferredLabel"]).size().rename("alt_matches")
    links = pd.concat([p, a], axis=1).fillna(0).reset_index()
    links["matches"] = links.pref_matches + links.alt_matches
    drop = (links.pref_matches == 0) & (links.alt_matches < 2)
    dropped = int(drop.sum())
    links = links[~drop].copy()
    links["link_type"] = links.pref_matches.gt(0).map({True: "title_preferred", False: "title_alternative"})

    # Rule 3: ISCO fallback for groups with fewer than MIN_LINKS links.
    main_isco = pd.read_csv(proc / "soc2020_isco08.csv", dtype=str).set_index("soc2020")["isco08"]
    counts = links.groupby("soc2020").size()
    thin = [s for s in sorted(idx.soc2020.unique()) if counts.get(s, 0) < MIN_LINKS]
    fb_rows = []
    for soc in thin:
        isco = main_isco.get(soc)
        have = set(links.loc[links.soc2020 == soc, "conceptUri"])
        for r in occ[occ.isco08 == isco].itertuples():
            if r.conceptUri not in have:
                fb_rows.append({"soc2020": soc, "conceptUri": r.conceptUri, "preferredLabel": r.preferredLabel,
                                "pref_matches": 0, "alt_matches": 0, "matches": 1, "link_type": "isco_fallback"})
    links = pd.concat([links, pd.DataFrame(fb_rows)], ignore_index=True)
    links["w_in_soc"] = links.matches / links.groupby("soc2020").matches.transform("sum")
    links = links.rename(columns={"conceptUri": "esco_uri", "preferredLabel": "esco_label"})
    links[["soc2020", "esco_uri", "esco_label", "link_type", "matches", "w_in_soc"]].to_csv(proc / "soc2020_esco_links.csv", index=False)

    titled = links[links.link_type != "isco_fallback"]
    print(f"title links: {len(titled)} (preferred {int((titled.link_type == 'title_preferred').sum())}, alternative {int((titled.link_type == 'title_alternative').sum())}); dropped single alternative-label links: {dropped}")
    print(f"SOC groups with >= {MIN_LINKS} title links: {(titled.groupby('soc2020').size() >= MIN_LINKS).sum()} of {idx.soc2020.nunique()}; using ISCO fallback: {len(thin)}")
    still_empty = sorted(set(idx.soc2020) - set(links.soc2020))
    print(f"groups with no link at all: {len(still_empty)} {still_empty}")


if __name__ == "__main__":
    main()
