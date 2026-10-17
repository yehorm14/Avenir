"""Parse extracted ASHE Table 14.7a/14.7b workbooks into one long table.

Usage: python -I ashe_parse.py ASHE_DIR OUT_DIR

ASHE_DIR holds one folder per year (from ashe_extract.py). Writes
OUT_DIR/ashe_long.parquet and OUT_DIR/ashe_long.csv with one row per
year x SOC 4-digit code x sheet (Full-Time, All):

year, edition, soc_version, soc_code, title, sheet, jobs_k, median, mean,
p10, p20, p25, p30, p40, p60, p70, p75, p80, p90, median_cv

Suppressed or missing cells ("x", "..", blanks) become NaN. median_cv is the
coefficient of variation of the median from table 14.7b (ONS quality guide:
<=5 precise, 5-10 reasonably precise, 10-20 use with caution, >20 suppressed).
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SHEETS = ["Full-Time", "All"]
FIXED = ["title", "soc_code", "jobs_k", "median", "median_change", "mean", "mean_change"]


def soc_version(year: int) -> int:
    return 2020 if year >= 2021 else 2010


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.strip().replace({"x": None, "..": None, "": None, "nan": None}), errors="coerce")


def read_sheet(path: Path, sheet: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip().eq("Description")][0]
    header = raw.iloc[header_row].tolist()
    cols = list(FIXED)
    for value in header[len(FIXED):]:
        try:
            cols.append(f"p{int(float(value))}")
        except (TypeError, ValueError):
            cols.append(f"extra_{len(cols)}")
    body = raw.iloc[header_row + 1:].copy()
    body.columns = cols[: body.shape[1]]
    body["soc_code"] = body["soc_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    body = body[body["soc_code"].str.fullmatch(r"\d{4}")]
    body["title"] = body["title"].astype(str).str.strip()
    for col in body.columns:
        if col not in ("title", "soc_code"):
            body[col] = to_num(body[col])
    return body


def parse_year(folder: Path) -> pd.DataFrame:
    year = int(folder.name.split("_")[0])
    edition = folder.name.split("_", 1)[1]
    table_a = next(p for p in folder.iterdir() if re.search(r"14\.7a", p.name))
    table_b = next((p for p in folder.iterdir() if re.search(r"14\.7b", p.name)), None)
    frames = []
    for sheet in SHEETS:
        a = read_sheet(table_a, sheet)
        keep = ["title", "soc_code", "jobs_k", "median", "mean"] + [c for c in a.columns if re.fullmatch(r"p\d+", c)]
        a = a[keep]
        if table_b is not None:
            b = read_sheet(table_b, sheet)[["soc_code", "median"]].rename(columns={"median": "median_cv"})
            a = a.merge(b, on="soc_code", how="left")
        else:
            a["median_cv"] = np.nan
        a.insert(0, "sheet", sheet)
        frames.append(a)
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "soc_version", soc_version(year))
    out.insert(0, "edition", edition)
    out.insert(0, "year", year)
    return out


def main() -> None:
    ashe_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = [parse_year(f) for f in sorted(ashe_dir.iterdir()) if f.is_dir()]
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(out_dir / "ashe_long.parquet", index=False)
    df.to_csv(out_dir / "ashe_long.csv", index=False)
    ft = df[df["sheet"] == "Full-Time"]
    summary = ft.groupby(["year", "soc_version"]).agg(
        codes=("soc_code", "nunique"),
        with_median=("median", lambda s: int(s.notna().sum())),
        with_jobs=("jobs_k", lambda s: int(s.notna().sum())),
        median_cv_present=("median_cv", lambda s: int(s.notna().sum())),
    )
    print(summary.to_string())
    print(f"rows: {len(df)}; written to {out_dir}")


if __name__ == "__main__":
    main()
