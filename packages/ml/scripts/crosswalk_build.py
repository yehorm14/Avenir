"""Build SOC 2010 <-> SOC 2020 and SOC 2020 -> ISCO-08 crosswalks.

Usage: python -I crosswalk_build.py RAW_DIR OUT_DIR

RAW_DIR must contain soc_crosswalk/ (ONS relationship tables, July 2021) and
soc_coding_index/soc2020_coding_index.xlsx. Writes to OUT_DIR:

- soc2020_from_soc2010.csv: soc2020, soc2010, weight. Share of people coded to
  the SOC 2020 unit group who were coded to each SOC 2010 group (LFS, men and
  women pooled; Census where the LFS base is empty). Use it to rebuild a
  SOC 2020 series from SOC 2010 data (e.g. pay as a weighted mean).
- soc2010_to_soc2020.csv: soc2010, soc2020, share. Where each SOC 2010 group's
  people went. Use it to split counts (e.g. jobs).
- soc2020_isco08.csv: soc2020, isco08, share, entries. ISCO-08 code most often
  assigned to the unit group's coding-index entries.
"""
import re
import sys
from pathlib import Path

import pandas as pd

CODE = re.compile(r"^(\d{4}):")


def parse_relationship(path: Path, sheet: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=0)
    # The SOC2010->2020 file suffixes columns with the year (men_lfs_base_2010).
    raw.columns = [re.sub(r"_(2010|2020)$", "", str(c)) for c in raw.columns]
    cols = raw.columns.tolist()
    src_col, dst_col = cols[0], cols[1]
    rows, current, bases = [], None, None
    for _, r in raw.iterrows():
        src = str(r[src_col]) if pd.notna(r[src_col]) else ""
        dst = str(r[dst_col]) if pd.notna(r[dst_col]) else ""
        m = CODE.match(src)
        if m and dst.strip().lower() == "total sample":
            current = m.group(1)
            bases = {k: (r[k] if pd.notna(r[k]) else 0) for k in cols if k.endswith("_base")}
            continue
        m2 = CODE.match(dst)
        if current and m2:
            num, den = 0.0, 0.0
            for group in ("men_lfs", "women_lfs"):
                b, p = bases.get(f"{group}_base", 0), r.get(f"{group}_perc")
                if b and pd.notna(p):
                    num += b * p
                    den += b
            if den == 0:
                for group in ("men_census", "women_census"):
                    b, p = bases.get(f"{group}_base", 0), r.get(f"{group}_perc")
                    if b and pd.notna(p):
                        num += b * p
                        den += b
            if den:
                rows.append((current, m2.group(1), num / den))
    return pd.DataFrame(rows, columns=["from_code", "to_code", "share"])


def main() -> None:
    raw_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    cw = raw_dir / "soc_crosswalk"

    comp = parse_relationship(cw / "soc2020soc2010relationshiptablesjuly2021.xlsx", "soc2020-soc2010-map_Unit")
    comp = comp.rename(columns={"from_code": "soc2020", "to_code": "soc2010", "share": "weight"})
    comp.to_csv(out_dir / "soc2020_from_soc2010.csv", index=False)

    split = parse_relationship(cw / "soc2010soc2020relationshiptablesjuly2021.xlsx",
                               next(s for s in pd.ExcelFile(cw / "soc2010soc2020relationshiptablesjuly2021.xlsx").sheet_names if s.endswith("Unit")))
    split = split.rename(columns={"from_code": "soc2010", "to_code": "soc2020"})
    split.to_csv(out_dir / "soc2010_to_soc2020.csv", index=False)

    idx = pd.read_excel(raw_dir / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index",
                        dtype=str, usecols=["SOC_2020", "ISCO-08 code based on SOC2020"])
    idx.columns = ["soc2020", "isco08"]
    idx = idx.dropna()
    idx = idx[idx["soc2020"].str.fullmatch(r"\d{4}") & idx["isco08"].str.fullmatch(r"\d{4}")]
    counts = idx.groupby(["soc2020", "isco08"]).size().rename("entries").reset_index()
    totals = counts.groupby("soc2020")["entries"].transform("sum")
    counts["share"] = counts["entries"] / totals
    best = counts.sort_values(["soc2020", "entries"], ascending=[True, False]).groupby("soc2020").head(1)
    best[["soc2020", "isco08", "share", "entries"]].to_csv(out_dir / "soc2020_isco08.csv", index=False)

    dom = comp.groupby("soc2020")["weight"].max()
    print(f"soc2020_from_soc2010: {comp['soc2020'].nunique()} SOC 2020 groups; dominant source share >=0.8: {(dom >= 0.8).sum()}, 0.5-0.8: {((dom >= 0.5) & (dom < 0.8)).sum()}, <0.5: {(dom < 0.5).sum()}")
    print(f"soc2010_to_soc2020: {split['soc2010'].nunique()} SOC 2010 groups")
    print(f"soc2020_isco08: {len(best)} SOC 2020 groups; mapping share >=0.8: {(best['share'] >= 0.8).sum()}")


if __name__ == "__main__":
    main()
