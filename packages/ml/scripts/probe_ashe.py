"""Probes on ASHE before any modelling. Nothing here is fitted to outcomes.

Usage: python -I probe_ashe.py PROCESSED_DIR

Probe A: how noisy are year-on-year changes in jobs counts vs median pay?
Probe B: a naive, pre-registered tier rule inside the SOC 2010 era
(no code bridging), checked against outcomes 5 years later.
  signal at base year Y (2013, 2014): pay rank at Y; prior jobs growth
  (2011 -> Y). Tiers are fixed thirds; no thresholds are tuned.
  outcomes: pay growth and jobs growth Y -> Y+5 (2018, 2019; avoids 2020).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(0)


def boot_ci(values: np.ndarray, stat=np.median, n: int = 2000) -> tuple[float, float]:
    values = values[~np.isnan(values)]
    if len(values) < 5:
        return (np.nan, np.nan)
    draws = [stat(rng.choice(values, size=len(values), replace=True)) for _ in range(n)]
    return (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)))


def main() -> None:
    df = pd.read_parquet(Path(sys.argv[1]) / "ashe_long.parquet")
    ft = df[(df.sheet == "Full-Time") & (df.soc_version == 2010)]
    wide_jobs = ft.pivot_table(index="soc_code", columns="year", values="jobs_k")
    wide_pay = ft.pivot_table(index="soc_code", columns="year", values="median")

    print("== Probe A: year-on-year change, SOC 2010 era, 2011-2019")
    for name, wide in (("jobs_k", wide_jobs), ("median pay", wide_pay)):
        yoy = np.log(wide.loc[:, 2012:2019].values / wide.loc[:, 2011:2018].values).ravel()
        yoy = yoy[np.isfinite(yoy)]
        print(f"{name:10s}: median |change| {np.median(np.abs(yoy)):.3f}; share |change|>20%: {np.mean(np.abs(yoy) > np.log(1.2)):.2%}; n={len(yoy)}")
    # Lag-1 autocorrelation of yearly jobs changes: negative means noise that reverses.
    ch = np.log(wide_jobs.loc[:, 2012:2019].values / wide_jobs.loc[:, 2011:2018].values)
    a, b = ch[:, :-1].ravel(), ch[:, 1:].ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    print(f"lag-1 autocorrelation of yearly jobs changes: {np.corrcoef(a[ok], b[ok])[0, 1]:.2f} (strongly negative = mostly sampling noise)")

    print("\n== Probe B: naive tiers, outcomes 5 years later (medians, 95% bootstrap CI)")
    for base in (2013, 2014):
        end = base + 5
        d = pd.DataFrame({
            "pay": wide_pay[base],
            "prior_jobs_growth": np.log(wide_jobs[base] / wide_jobs[2011]),
            "pay_growth": np.log(wide_pay[end] / wide_pay[base]),
            "jobs_growth": np.log(wide_jobs[end] / wide_jobs[base]),
        }).dropna()
        d["return_third"] = pd.qcut(d["pay"].rank(method="first"), 3, labels=["low", "mid", "high"])
        d["demand_third"] = pd.qcut(d["prior_jobs_growth"].rank(method="first"), 3, labels=["shrinking", "flat", "growing"])
        print(f"-- base {base} -> {end}: {len(d)} occupations with complete data")
        for col, groups in (("return_third", ["low", "high"]), ("demand_third", ["shrinking", "growing"])):
            for g in groups:
                sub = d[d[col] == g]
                for outcome in ("pay_growth", "jobs_growth"):
                    med = float(np.median(sub[outcome]))
                    lo, hi = boot_ci(sub[outcome].values)
                    decline = float(np.mean(sub["jobs_growth"] < 0)) if outcome == "jobs_growth" else np.nan
                    extra = f"; share jobs fell {decline:.0%}" if outcome == "jobs_growth" else ""
                    print(f"   {col:13s} {g:9s} {outcome:11s} median {med:+.3f} [{lo:+.3f}, {hi:+.3f}]{extra}")
        rho_pay = d[["pay", "pay_growth"]].corr(method="spearman").iloc[0, 1]
        rho_dem = d[["prior_jobs_growth", "jobs_growth"]].corr(method="spearman").iloc[0, 1]
        print(f"   spearman: pay level vs later pay growth {rho_pay:+.2f}; prior jobs growth vs later jobs growth {rho_dem:+.2f}")


if __name__ == "__main__":
    main()
