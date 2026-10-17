"""Probe: bridge SOC 2010 ASHE (2011-2020) onto SOC 2020 codes, then check it.

Usage: python -I probe_bridge.py PROCESSED_DIR CPIH_CSV

- Pay for a SOC 2020 code in 2011-2020 = weighted mean of its SOC 2010 source
  medians (composition weights, renormalised over sources with data).
- Jobs = sum over SOC 2010 groups of (share going to the SOC 2020 code) x jobs.
- Seam test: bridged 2020 vs native 2021. If bridging works, pay ratios sit
  near one year of growth and job ratios near 1.
- Real pay uses CPIH (April, the ASHE reference month).
- COVID shock measured natively in SOC 2010 (2019 -> 2020), then mapped.
Nothing is fitted; this is a check before building the real series.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CASES = ["2134", "3544", "2433", "2422", "3412", "2451", "2142", "5241", "2313", "2254"]


def cpih_april(path: str) -> dict[int, float]:
    df = pd.read_csv(path, header=None, names=["period", "value"])
    df = df[df["period"].astype(str).str.fullmatch(r"\d{4} APR")]
    return {int(p[:4]): float(v) for p, v in zip(df["period"], df["value"])}


def main() -> None:
    proc = Path(sys.argv[1])
    cpi = cpih_april(sys.argv[2])
    a = pd.read_parquet(proc / "ashe_long.parquet")
    a = a[a.sheet == "Full-Time"]
    comp = pd.read_csv(proc / "soc2020_from_soc2010.csv", dtype={"soc2020": str, "soc2010": str})
    split = pd.read_csv(proc / "soc2010_to_soc2020.csv", dtype={"soc2010": str, "soc2020": str})
    old = a[a.soc_version == 2010][["year", "soc_code", "median", "jobs_k"]].rename(columns={"soc_code": "soc2010"})
    new = a[a.soc_version == 2020][["year", "soc_code", "title", "median", "jobs_k"]].rename(columns={"soc_code": "soc2020"})
    titles = new.drop_duplicates("soc2020").set_index("soc2020")["title"]

    pay = comp.merge(old, on="soc2010").dropna(subset=["median"])
    pay = pay[pay["weight"] > 0]
    pay["wx"] = pay["weight"] * pay["median"]
    sums = pay.groupby(["soc2020", "year"])[["wx", "weight"]].sum()
    bridged_pay = (sums["wx"] / sums["weight"]).rename("median")
    jobs = split.merge(old, on="soc2010").dropna(subset=["jobs_k"])
    jobs["part"] = jobs["share"] * jobs["jobs_k"]
    bridged_jobs = jobs.groupby(["soc2020", "year"])["part"].sum().rename("jobs_k")
    bridged = pd.concat([bridged_pay, bridged_jobs], axis=1).reset_index()
    bridged["bridged"] = True
    native = new.drop(columns="title").assign(bridged=False)
    series = pd.concat([bridged, native], ignore_index=True)
    series["real_median_2025gbp"] = series["median"] * cpi[2025] / series["year"].map(cpi)
    series.to_csv(proc / "probe_soc2020_series.csv", index=False)

    print("== Seam test: bridged 2020 vs native 2021 (SOC 2020 codes)")
    s20 = series[(series.year == 2020) & series.bridged].set_index("soc2020")
    s21 = series[(series.year == 2021) & ~series.bridged].set_index("soc2020")
    for col in ("median", "jobs_k"):
        r = (s21[col] / s20[col]).replace([np.inf, -np.inf], np.nan).dropna()
        print(f"{col:7s}: n={len(r)}; median ratio {r.median():.3f}; IQR [{r.quantile(.25):.3f}, {r.quantile(.75):.3f}]; outside [0.8, 1.25]: {np.mean((r < 0.8) | (r > 1.25)):.1%}")
    print(f"(CPIH Apr 2020->2021: {cpi[2021] / cpi[2020] - 1:+.1%})")

    print("\n== Case studies (full-time employees; real pay in 2025 GBP)")
    for code in CASES:
        g = series[series.soc2020 == code].set_index("year").sort_index()
        if g.empty:
            continue
        def val(y, c):
            return g.loc[y, c] if y in g.index and pd.notna(g.loc[y, c]) else np.nan
        rp11, rp25 = val(2011, "real_median_2025gbp"), val(2025, "real_median_2025gbp")
        print(f"{code} {titles.get(code, '?')[:48]:48s} jobs k 2011 {val(2011, 'jobs_k'):6.1f} | 2019 {val(2019, 'jobs_k'):6.1f} | 2021 {val(2021, 'jobs_k'):6.1f} | 2025 {val(2025, 'jobs_k'):6.1f}"
              f" || real pay 2011 {rp11:8.0f} -> 2025 {rp25:8.0f} ({(rp25 / rp11 - 1) if rp11 else np.nan:+.1%})")

    print("\n== COVID, native SOC 2010: change 2019 -> 2020 (full-time employees)")
    w = old.pivot_table(index="soc2010", columns="year", values=["jobs_k", "median"])
    d = pd.DataFrame({
        "jobs_19": w[("jobs_k", 2019)], "jobs_chg": np.log(w[("jobs_k", 2020)] / w[("jobs_k", 2019)]),
        "real_pay_chg": np.log((w[("median", 2020)] / cpi[2020]) / (w[("median", 2019)] / cpi[2019])),
    }).dropna()
    big = d[d.jobs_19 >= 20]
    print(f"all occupations: median jobs change {d.jobs_chg.median():+.3f}; median real pay change {d.real_pay_chg.median():+.3f}; n={len(d)}; with >=20k jobs n={len(big)}")
    t10 = old[old.year == 2019].set_index("soc2010")
    a10 = pd.read_parquet(proc / "ashe_long.parquet")
    names10 = a10[(a10.soc_version == 2010)].drop_duplicates("soc_code").set_index("soc_code")["title"]
    for label, part in (("held up best", big.nlargest(6, "jobs_chg")), ("hit hardest", big.nsmallest(6, "jobs_chg"))):
        print(f"-- {label} (>=20k jobs):")
        for code, r in part.iterrows():
            print(f"   {code} {names10.get(code, '?')[:50]:50s} jobs {r.jobs_chg:+.2f}  real pay {r.real_pay_chg:+.2f}")


if __name__ == "__main__":
    main()
