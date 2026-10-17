"""Probe: how much does the ILO exposure score vary inside one SOC 2020 group?

Usage: python -I probe_isco.py RAW_DIR PROCESSED_DIR

The ONS coding index assigns each UK job title a SOC 2020 code and an ISCO-08
code. One SOC 2020 group can contain titles that ISCO splits across several
codes, each with its own ILO score. This measures the spread of those scores
within each SOC group, to show whether the join method actually matters.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    raw, proc = Path(sys.argv[1]), Path(sys.argv[2])
    idx = pd.read_excel(raw / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index",
                        dtype=str, usecols=["SOC_2020", "ISCO-08 code based on SOC2020"])
    idx.columns = ["soc2020", "isco08"]
    idx = idx.dropna()
    idx = idx[idx.soc2020.str.fullmatch(r"\d{4}") & idx.isco08.str.fullmatch(r"\d{4}")]
    ilo = pd.read_csv(proc / "ilo_exposure.csv", dtype={"isco08": str})
    m = idx.groupby(["soc2020", "isco08"]).size().rename("entries").reset_index().merge(ilo[["isco08", "exposure_mean"]], on="isco08", how="left")
    m["share"] = m.entries / m.groupby("soc2020").entries.transform("sum")
    covered = m.dropna(subset=["exposure_mean"])
    rows = []
    for soc, g in covered.groupby("soc2020"):
        w = g.share / g.share.sum()
        mean = float(np.sum(w * g.exposure_mean))
        sd = float(np.sqrt(np.sum(w * (g.exposure_mean - mean) ** 2)))
        dom = g.loc[g.share.idxmax(), "exposure_mean"]
        rows.append((soc, len(g), mean, float(dom), sd, float(g.exposure_mean.max() - g.exposure_mean.min()), float(g.share.sum())))
    r = pd.DataFrame(rows, columns=["soc2020", "n_isco", "weighted", "dominant", "within_sd", "range", "share_with_score"])
    r["diff"] = (r.weighted - r.dominant).abs()
    print(f"SOC 2020 groups with any ILO score: {len(r)} of {idx.soc2020.nunique()}")
    print(f"groups mapping to 1 ISCO code: {(r.n_isco == 1).sum()}; 2-3: {r.n_isco.between(2, 3).sum()}; 4+: {(r.n_isco >= 4).sum()}")
    print(f"range of ILO scores inside a group: median {r['range'].median():.3f}; >0.10: {(r['range'] > 0.10).sum()}; >0.20: {(r['range'] > 0.20).sum()}")
    print(f"|weighted - dominant|: median {r['diff'].median():.3f}; >0.05: {(r['diff'] > 0.05).sum()}; >0.10: {(r['diff'] > 0.10).sum()}")
    print("ILO scale for reference: 'Not exposed' ~0.1-0.35, 'Gradient 4' ~0.7+")
    no_score = sorted(set(idx.soc2020) - set(r.soc2020))
    print(f"groups with no ILO score at all: {len(no_score)} -> {no_score}")
    print("largest within-group spreads:")
    print(r.sort_values("range", ascending=False).head(6).to_string(index=False))
    r.to_csv(proc / "probe_isco_spread.csv", index=False)


if __name__ == "__main__":
    main()
