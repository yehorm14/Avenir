"""Build SOC 2000 <-> SOC 2010 crosswalk weights from the ONS relationship tables.

Usage: python -I crosswalk_2000.py RAW_DIR OUT_DIR

Table 1a: for each SOC 2010 unit group, % of its cases coded to each SOC 2000 group
(composition). Table 1b: for each SOC 2000 group, % going to each SOC 2010 group
(split). Tables 2b / 2a give the bases. Shares pool men and women from the LFS
Jan-Mar 2007 dual-coded sample (LFSJM07), falling back to Census 2001 where the LFS
base is empty. "_" (below threshold) counts as 0; "*" (small base) is kept.

Writes OUT_DIR/soc2010_from_soc2000.csv (soc2010, soc2000, weight) and
OUT_DIR/soc2000_to_soc2010.csv (soc2000, soc2010, share). Weights are renormalised
to sum to 1 per group, since ONS only lists destinations above a threshold.
"""
import re
import sys
from pathlib import Path

import pandas as pd

HEADER = re.compile(r"^(\d{4})\s")


def pct(x) -> float:
    s = str(x).strip().replace("*", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def bases(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Unit", header=None).iloc[2:, :7]
    df.columns = ["code", "m_lfs", "m_cen", "m_96", "f_lfs", "f_cen", "f_96"]
    df["code"] = df["code"].astype(str).str.replace(r"\.0$", "", regex=True)
    df = df[df.code.str.fullmatch(r"\d{4}")]
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df.set_index("code")


def parse(table: Path, base: pd.DataFrame, group_name: str, member_name: str) -> pd.DataFrame:
    raw = pd.read_excel(table, sheet_name="Unit", header=None).iloc[2:]
    rows, current = [], None
    for r in raw.itertuples(index=False):
        first, member = str(r[0]).strip(), str(r[3]).strip().replace(".0", "")
        m = HEADER.match(first)
        if m and (member in ("nan", "")):
            current = m.group(1)
            continue
        if current and re.fullmatch(r"\d{4}", member):
            b = base.loc[current] if current in base.index else None
            if b is not None and (b.m_lfs + b.f_lfs) > 0:
                w = (pct(r[0]) * b.m_lfs + pct(r[7]) * b.f_lfs) / (b.m_lfs + b.f_lfs)
            elif b is not None and (b.m_cen + b.f_cen) > 0:
                w = (pct(r[1]) * b.m_cen + pct(r[6]) * b.f_cen) / (b.m_cen + b.f_cen)
            else:
                w = (pct(r[0]) + pct(r[7])) / 2
            rows.append((current, member, w / 100))
    df = pd.DataFrame(rows, columns=[group_name, member_name, "w"])
    df = df[df.w > 0]
    df["w"] = df.w / df.groupby(group_name).w.transform("sum")
    return df


def main() -> None:
    raw, out = Path(sys.argv[1]) / "soc_crosswalk_2000", Path(sys.argv[2])
    comp = parse(raw / "Table 1a.xls", bases(raw / "Table 2b.xls"), "soc2010", "soc2000").rename(columns={"w": "weight"})
    split = parse(raw / "Table 1b.xls", bases(raw / "Table 2a.xls"), "soc2000", "soc2010").rename(columns={"w": "share"})
    comp.to_csv(out / "soc2010_from_soc2000.csv", index=False)
    split.to_csv(out / "soc2000_to_soc2010.csv", index=False)
    dom = comp.groupby("soc2010").weight.max()
    print(f"soc2010_from_soc2000: {comp.soc2010.nunique()} SOC 2010 groups; dominant source >=0.8: {(dom >= 0.8).sum()}, 0.5-0.8: {((dom >= 0.5) & (dom < 0.8)).sum()}, <0.5: {(dom < 0.5).sum()}")
    print(f"soc2000_to_soc2010: {split.soc2000.nunique()} SOC 2000 groups")


if __name__ == "__main__":
    main()
