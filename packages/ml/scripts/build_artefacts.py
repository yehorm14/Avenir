"""Build the ML artefacts (contract v1.2) for every SOC 2020 occupation, plus the mock set.

Usage: python -I build_artefacts.py RAW_DIR PROCESSED_DIR SNAPSHOT_DIR

Writes SNAPSHOT_DIR/*.json (all occupations) and SNAPSHOT_DIR/mock/*.json (the 20 demo careers
plus their hedge candidates, same shapes). Inputs come from ashe_parse, crosswalk_build,
crosswalk_2000, ilo_parse, esco_link, hedges_build, validate_hedges and category_map_build
(packages/ml/data/category_map.csv, committed).

Each stage owns its outputs: this script never overwrites a real fit.json (m1_matcher build-fit
owns it) and merges its checks into eval.json instead of replacing the file (m1_matcher and
m2_exposure_check add their own checks).

Rules (docs/decisions.md; the v1.2 changes follow two independent reviews):
- Inflation: CPIH averaged over the tax year ending 5 April, the period ASHE annual pay covers.
- Pay bridges across code changes; job counts don't. Every bridged value carries the crosswalk's
  purity (how much of the old group's workforce the new group is) and coverage (how much of the
  source weight had data). Purity below 0.5 adds `bridged_low_purity`; coverage below 0.8 adds
  `partial_sources`. Both force low confidence.
- Demand: ONS calls ASHE job counts indicative, and 2021-22 were distorted by occupation
  miscoding, so the current trend uses 2022-2025 and is measured against the typical occupation.
- Crises are published relative to the median occupation. Each one faces a placebo test (is the
  spread between careers in the crisis window clearly larger than in ordinary years?). Crises
  that fail stay in the files, flagged show_on_card: false.
- Confidence: one rule for every metric (ml_common.cap_confidence, contract section 2.4).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from ml_common import (AFFINITY, DEMO, NOW, SCHEMA_VERSION, SOURCES, TAGS, assign_tiers, boot, cpih_taxyear,  # noqa: E402
                       cv_conf, load_json, metric, num, theil, trend_conf, weighted_map, write)

CATEGORY_MAP = Path(__file__).resolve().parents[1] / "data" / "category_map.csv"
CRISIS_MIN_JOBS_K = 50     # crisis job changes use the occupation's own count only above this (agreed 17 Oct)
MAX_PAY_CV = 10            # pay changes use the occupation's own median only when ONS's CV is at most this
TREND_MIN_MEAN_K = 20      # trends on smaller counts (rounded to the thousand) are at most low confidence
PURITY_MIN = 0.5
COVERAGE_MIN = 0.8
BRIDGE_SD = 0.06           # per-occupation bridging error (median seam error about 4%, p90 14%)
BRIDGE_SD_LOW_PURITY = 0.15
PLACEBO_MIN_RATIO = 1.25   # crisis spread must be at least 25% above the ordinary-year median to go on cards
CURRENT_YEARS = list(range(2022, 2026))
PREVIOUS_YEARS = list(range(2011, 2020))
VOLATILE_NOTE = "The ONS flagged this job-advert category as unreliable over the period, so no value is shown."


def piv(df, version, col):
    return df[df.soc_version == version].pivot_table(index="soc_code", columns="year", values=col)


def col(panel: pd.DataFrame, year) -> pd.Series:
    return panel[year] if year in panel.columns else pd.Series(dtype=float)


def rel_change(new: pd.Series, old: pd.Series) -> pd.Series:
    return np.log(new / old).replace([np.inf, -np.inf], np.nan)


def robust_sd(x) -> float:
    x = pd.Series(x, dtype=float).dropna()
    return float((x.quantile(0.75) - x.quantile(0.25)) / 1.349) if len(x) >= 20 else float("nan")


def own_or_parent(rel4: pd.Series, ok4: pd.Series, grel: pd.Series, codes) -> tuple[pd.Series, pd.Series]:
    """Per 4-digit code: its own log change where ok4, else its 3-digit parent's. Returns (values, parent indicator)."""
    vals, par = {}, {}
    for code in codes:
        if bool(ok4.get(code, False)) and pd.notna(rel4.get(code)):
            vals[code], par[code] = float(rel4[code]), 0.0
        elif pd.notna(grel.get(code[:3])):
            vals[code], par[code] = float(grel[code[:3]]), 1.0
    return pd.Series(vals, dtype=float), pd.Series(par, dtype=float)


def jobs_change(new, old, gnew, gold):
    rel4 = rel_change(new, old)
    ok = old.reindex(rel4.index) >= CRISIS_MIN_JOBS_K
    return own_or_parent(rel4, ok, rel_change(gnew, gold), old.index.union(new.index))


def pay_change(new, old, cv_new, cv_old, gnew, gold):
    """Log change in (already deflated) pay; own medians only when both CVs are at most MAX_PAY_CV."""
    rel4 = rel_change(new, old)
    ok = (cv_new.reindex(rel4.index) <= MAX_PAY_CV) & (cv_old.reindex(rel4.index) <= MAX_PAY_CV)
    return own_or_parent(rel4, ok, rel_change(gnew, gold), old.index.union(new.index))


def placebo(window: pd.Series, ordinary: list[pd.Series], label: str) -> dict:
    """Is the cross-career spread in the crisis window larger than in ordinary windows?"""
    w = robust_sd(window)
    sds = [s for s in (robust_sd(v) for v in ordinary) if not math.isnan(s)]
    med = float(np.median(sds)) if sds else float("nan")
    ratio = w / med if sds and med > 0 else float("nan")
    return {"measure": label, "window_robust_sd": num(w), "ordinary_robust_sd_median": num(med),
            "ordinary_robust_sd_range": [num(min(sds)), num(max(sds))] if sds else None, "n_ordinary_windows": len(sds),
            "ratio": num(ratio, 3), "passes": bool(ratio >= PLACEBO_MIN_RATIO) if not math.isnan(ratio) else False,
            "rule": f"Shown on cards only if the spread between careers (robust SD) is at least {PLACEBO_MIN_RATIO:.2f}x the ordinary-year median"}


def year_index(panel: pd.DataFrame, years: list[int]) -> pd.Series:
    """Cumulative median log change across occupations: the typical occupation's path. It absorbs
    year-wide effects such as survey reweighting, so trends measured against it cancel them."""
    idx = {years[0]: 0.0}
    for y0, y1 in zip(years, years[1:]):
        ch = rel_change(col(panel, y1), col(panel, y0)).dropna()
        idx[y1] = idx[y0] + (float(ch.median()) if len(ch) else 0.0)
    return pd.Series(idx)


def relative_trend(counts: list, years: list[int], index: pd.Series, cvs: list, min_points: int):
    """Theil-Sen trend of counts against the typical occupation's path, with the interval widened
    to at least the sampling noise implied by ONS's CVs. Returns a dict or None."""
    c = np.asarray(counts, float)
    ok = np.isfinite(c) & (c > 0)
    if ok.sum() < min_points:
        return None
    adj = c / np.exp(index.reindex(years).values)
    rel = theil(years, adj, min_points=min_points)
    absolute = theil(years, c, min_points=min_points)
    if rel is None:
        return None
    x = np.asarray(years, float)[ok]
    sxx = float(((x - x.mean()) ** 2).sum())
    cv = np.asarray(cvs, float)[ok]
    sigma = float(np.nanmean(cv)) / 100 if np.isfinite(cv).any() else 0.0
    half_cv = 1.645 * sigma / math.sqrt(sxx) if sxx > 0 else 0.0
    s, lo, hi = (math.log1p(v) for v in rel)
    lo, hi = min(lo, s - half_cv), max(hi, s + half_cv)
    return {"value": math.expm1(s), "low": math.expm1(lo), "high": math.expm1(hi), "absolute": absolute[0] if absolute else None,
            "mean_k": float(np.nanmean(c[ok])), "distinct": int(len(set(np.round(c[ok], 1)))), "n": int(ok.sum())}


def trend_confidence(t: dict) -> str:
    conf = trend_conf(t["high"] - t["low"])
    if t["mean_k"] < TREND_MIN_MEAN_K or t["distinct"] < 3:
        conf = "low"
    return conf


def main() -> None:
    raw, proc, snap = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    cpi = cpih_taxyear(raw / "ons_cpih" / "cpih_index_l522.csv")
    a = pd.read_parquet(proc / "ashe_long.parquet")
    grp = pd.read_parquet(proc / "ashe_groups.parquet")
    comp = pd.read_csv(proc / "soc2020_from_soc2010.csv", dtype={"soc2020": str, "soc2010": str})
    split = pd.read_csv(proc / "soc2010_to_soc2020.csv", dtype={"soc2010": str, "soc2020": str})
    comp0 = pd.read_csv(proc / "soc2010_from_soc2000.csv", dtype={"soc2010": str, "soc2000": str})
    ilo = pd.read_csv(proc / "ilo_exposure.csv", dtype={"isco08": str})
    catmap = pd.read_csv(CATEGORY_MAP, dtype={"soc2020": str}).set_index("soc2020")
    provisional_years = set(a[a.edition.astype(str).str.contains("provisional")].year.astype(int))

    FT, ALL = a[a.sheet == "Full-Time"], a[a.sheet == "All"]
    GFT, GALL = grp[(grp.sheet == "Full-Time") & (grp.level == 3)], grp[(grp.sheet == "All") & (grp.level == 3)]
    pay20, cv20, jobs20, jobscv20 = piv(FT, 2020, "median"), piv(FT, 2020, "median_cv"), piv(FT, 2020, "jobs_k"), piv(FT, 2020, "jobs_k_cv")
    jobsall20, jobsallcv20 = piv(ALL, 2020, "jobs_k"), piv(ALL, 2020, "jobs_k_cv")
    gpay20, gcv20, gjobs20, gjobscv20 = piv(GFT, 2020, "median"), piv(GFT, 2020, "median_cv"), piv(GFT, 2020, "jobs_k"), piv(GFT, 2020, "jobs_k_cv")
    pay10, cv10, jobs10, jobscv10 = piv(FT, 2010, "median"), piv(FT, 2010, "median_cv"), piv(FT, 2010, "jobs_k"), piv(FT, 2010, "jobs_k_cv")
    gjobsall20, gjobsallcv20 = piv(GALL, 2020, "jobs_k"), piv(GALL, 2020, "jobs_k_cv")
    jobsall10, gjobsall10 = piv(ALL, 2010, "jobs_k"), piv(GALL, 2010, "jobs_k")
    pay00, cv00, jobsall00, gjobsall00 = piv(FT, 2000, "median"), piv(FT, 2000, "median_cv"), piv(ALL, 2000, "jobs_k"), piv(GALL, 2000, "jobs_k")
    gpay00 = piv(GFT, 2000, "median")
    now = FT[FT.year == 2025].set_index("soc_code")
    gnow = GFT[GFT.year == 2025].set_index("soc_code")
    titles = now.title.to_dict()
    socs = sorted(now.index)
    missing_cat = sorted(set(socs) - set(catmap.index))
    if missing_cat:
        raise SystemExit(f"category_map.csv has no category for {missing_cat}; rerun category_map_build.py")

    def to20(values10: pd.Series) -> pd.DataFrame:
        return weighted_map(values10.dropna().rename_axis("soc2010"), comp, "soc2010", "soc2020")

    def to10(values00: pd.Series) -> pd.DataFrame:
        return weighted_map(values00.dropna().rename_axis("soc2000"), comp0, "soc2000", "soc2010")

    comp_total = comp[comp.weight > 0].groupby("soc2020").weight.sum()

    def jobs_to20(jobs: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Split SOC 2010 counts into SOC 2020 codes; coverage = share of the new code's workforce
        whose source code has a published count that year."""
        j = split.merge(jobs.dropna().rename("v").rename_axis("soc2010").reset_index(), on="soc2010")
        counts = (j.share * j.v).groupby(j.soc2020).sum()
        have = set(jobs.dropna().index)
        cov = comp[(comp.weight > 0) & comp.soc2010.isin(have)].groupby("soc2020").weight.sum() / comp_total
        return counts, cov.reindex(counts.index).fillna(0.0)

    # Purity: how much of the source groups' workforce lands in the new code, weighted by where the
    # new code's workforce came from. Low purity means the old group's figures describe other jobs.
    pur = comp[comp.weight > 0].merge(split, on=["soc2010", "soc2020"], how="left").fillna({"share": 0.0})
    purity = (pur.weight * pur.share).groupby(pur.soc2020).sum() / pur.groupby("soc2020").weight.sum()
    dominant10 = comp.groupby("soc2020").weight.max()

    # ---------------- Pay path 2007-2025 (bridged before 2021) and bridged jobs 2011-2020 ----------------
    pay_by_year, paycov_by_year, jobs_by_year, jobscov_by_year = {}, {}, {}, {}
    for y in range(2007, 2011):
        step1 = to10(col(pay00, y))
        step2 = to20(step1["value"])
        pay_by_year[y] = step2["value"]
        paycov_by_year[y] = step2["coverage"] * to20(step1["coverage"])["value"].reindex(step2.index).fillna(0.0)
    for y in range(2011, 2021):
        m10 = to20(col(pay10, y))
        pay_by_year[y], paycov_by_year[y] = m10["value"], m10["coverage"]
        jobs_by_year[y], jobscov_by_year[y] = jobs_to20(col(jobs10, y))
    for y in range(2021, 2026):
        pay_by_year[y], paycov_by_year[y] = col(pay20, y), pd.Series(1.0, index=col(pay20, y).index)
        jobs_by_year[y] = col(jobs20, y)

    def clean_jobs(y: int) -> pd.Series:
        """Bridged counts with less than 80% source coverage are blanked, not shown as undercounts."""
        if y >= 2021:
            return jobs_by_year[y]
        return jobs_by_year[y].where(jobscov_by_year[y] >= COVERAGE_MIN)

    history = {}
    for soc in socs:
        low_purity = purity.get(soc, 1.0) < PURITY_MIN
        pts = []
        for y in range(2007, 2026):
            p = pay_by_year[y].get(soc, np.nan)
            pc = paycov_by_year[y].get(soc, 0.0)
            if y <= 2020 and pc < 0.5:
                p = np.nan
            jk = clean_jobs(y).get(soc, np.nan) if y >= 2011 else np.nan
            flags = []
            if y <= 2010:
                flags += ["bridged_soc2000", "bridged_soc2010"]
            elif y <= 2020:
                flags.append("bridged_soc2010")
            if y <= 2020 and low_purity:
                flags.append("bridged_low_purity")
            if y <= 2020 and pd.notna(p) and pc < COVERAGE_MIN:
                flags.append("partial_sources")
            if y == 2020:
                flags.append("covid_year")
            if y in provisional_years:
                flags.append("provisional")
            if y >= 2021:
                flags.append("recoded_2021")
            if pd.isna(p) and pd.isna(jk):
                continue
            pts.append({"year": y, "pay_median": num(p, 0), "pay_median_real": num(p * cpi[2025] / cpi[y], 0) if pd.notna(p) else None,
                        "jobs_k": num(jk, 1), "flags": flags})
        history[soc] = pts
    real_pay = {y: pay_by_year[y] * cpi[2025] / cpi[y] for y in pay_by_year}

    # ---------------- Exposure: ILO weighted over ISCO codes, DfE percentile cross-check ----------------
    idx = pd.read_excel(raw / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index", dtype=str,
                        usecols=["SOC_2020", "ISCO-08 code based on SOC2020"])
    idx.columns = ["soc2020", "isco08"]
    idx = idx.dropna()
    idx = idx[idx.soc2020.str.fullmatch(r"\d{4}") & idx.isco08.str.fullmatch(r"\d{4}")]
    isco = idx.groupby(["soc2020", "isco08"]).size().rename("n").reset_index()
    isco["share"] = isco.n / isco.groupby("soc2020").n.transform("sum")
    isco = isco.merge(ilo[["isco08", "gradient", "exposure_mean", "exposure_sd"]], on="isco08", how="left")
    isco["direct"] = isco.exposure_mean.notna()
    # Missing means missing (Avenir rule 3): unscored ISCO codes (e.g. 1439, armed forces) are not filled
    # with averages; the share of job titles that do have a score is published and gates the value.
    expo = {}
    for soc, g in isco.groupby("soc2020"):
        s_ = g[g.direct]
        coverage = float(s_.share.sum())
        if s_.empty or coverage < 0.5:
            continue
        w = s_.share / s_.share.sum()
        mean = float((w * s_.exposure_mean).sum())
        between = float(np.sqrt((w * (s_.exposure_mean - mean) ** 2).sum()))
        within = float(np.sqrt((w * s_.exposure_sd.fillna(0) ** 2).sum()))
        top = s_.loc[s_.share.idxmax()]
        expo[soc] = {"mean": mean, "half": math.sqrt(between ** 2 + within ** 2), "between": between, "within": within,
                     "gradient": top["gradient"] if pd.notna(top["gradient"]) else None, "dominant_isco": top["isco08"],
                     "n_isco": int(len(s_)), "coverage": coverage}
    expo_cov = isco[isco.direct].groupby("soc2020").share.sum()
    ilo_vals = pd.Series({k: v["mean"] for k, v in expo.items()})
    ilo_pct = ilo_vals.rank(pct=True)
    dfe = pd.read_excel(raw / "dfe_ai" / "Annex_1_-_Impact_of_AI_on_UK_jobs_and_training_data_sources.xlsx", sheet_name="AIOE by education level", header=2)
    dfe["soc2010"] = dfe["SOC"].astype(str).str.extract(r"(\d{4})")[0]
    dfe = dfe.dropna(subset=["soc2010", "LLM"]).drop_duplicates("soc2010").set_index("soc2010")["LLM"].astype(float)
    dfe20 = to20(dfe)
    dfe_pct = dfe20["value"].rank(pct=True)
    both = ilo_vals.to_frame("ilo").join(dfe20["value"].rename("dfe"), how="inner").dropna()
    rho = float(spearmanr(both.ilo, both.dfe).statistic)
    within_rows = []
    for g2, g in both.groupby(both.index.str[:2]):
        if len(g) >= 5:
            within_rows.append((len(g), float(spearmanr(g.ilo, g.dfe).statistic)))
    rho_within2 = sum(n * r for n, r in within_rows) / sum(n for n, _ in within_rows)

    # ---------------- Crises (each centred on the median occupation; each faces a placebo test) ----------------
    covid_raw, covid_par = jobs_change(col(jobsall10, 2020), col(jobsall10, 2019), col(gjobsall10, 2020), col(gjobsall10, 2019))
    covid20, covid_par20 = to20(covid_raw), to20(covid_par)
    big10 = lambda y0, y1: rel_change(col(jobsall10, y1), col(jobsall10, y0))[col(jobsall10, y0) >= CRISIS_MIN_JOBS_K]  # noqa: E731
    big00 = lambda y0, y1: rel_change(col(jobsall00, y1), col(jobsall00, y0))[col(jobsall00, y0) >= CRISIS_MIN_JOBS_K]  # noqa: E731
    ordinary_jobs = [big10(y, y + 1) for y in range(2011, 2019)]
    pl_covid = placebo(big10(2019, 2020), ordinary_jobs, "all-employee jobs, one-year log change, occupations with at least 50,000 jobs")

    # 2008: jobs only (annual pay "2009" is the tax year April 2008 - March 2009, mostly before the crash).
    gfc_raw, gfc_par = jobs_change(col(jobsall00, 2009), col(jobsall00, 2008), col(gjobsall00, 2009), col(gjobsall00, 2008))
    gfc20 = to20(to10(gfc_raw)["value"])
    gfc_par20 = to20(to10(gfc_par)["value"])
    gfc_pay_raw, _ = pay_change(col(pay00, 2009) / cpi[2009], col(pay00, 2008) / cpi[2008], col(cv00, 2009), col(cv00, 2008),
                                col(gpay00, 2009) / cpi[2009], col(gpay00, 2008) / cpi[2008])
    gfc_pay20 = to20(to10(gfc_pay_raw)["value"])["value"]
    pl_gfc = placebo(big00(2008, 2009), [big00(2007, 2008), big00(2009, 2010)] + ordinary_jobs,
                     "all-employee jobs, one-year log change, occupations with at least 50,000 jobs")

    # Cost of living: real pay from tax year 2022/23 (peak inflation) to 2024/25, i.e. who recovered.
    col_raw, col_par = pay_change(col(pay20, 2025) / cpi[2025], col(pay20, 2023) / cpi[2023], col(cv20, 2025), col(cv20, 2023),
                                  col(gpay20, 2025) / cpi[2025], col(gpay20, 2023) / cpi[2023])

    def own_pay2(p, cv, y0, y1):
        r = rel_change(col(p, y1), col(p, y0))
        return r[(col(cv, y1).reindex(r.index) <= MAX_PAY_CV) & (col(cv, y0).reindex(r.index) <= MAX_PAY_CV)]
    pl_col = placebo(own_pay2(pay20, cv20, 2023, 2025), [own_pay2(pay10, cv10, y, y + 2) for y in range(2011, 2018)],
                     "full-time median pay, two-year log change, occupations with CV at most 10%")

    # Tech slump: de-duplicated adverts, the same calendar months in both years.
    adv = pd.read_excel(raw / "ons_online_adverts" / "onlinejobadvertestimatesdataset241024.xlsx", sheet_name="Adverts by category Feb 2020 DD", header=6)
    adv = adv.dropna(subset=["Date"]).set_index("Date")
    adv = adv[[c for c in adv.columns if c != "Notes"]].apply(pd.to_numeric, errors="coerce")
    peak, slump = adv.loc["2022-01-01":"2022-06-30"].mean(), adv.loc["2024-01-01":"2024-06-30"].mean()
    tech = np.log(slump / peak)
    covid_adv = np.log(adv.loc["2020-04-01":"2020-06-30"].mean() / 100.0)
    covid_adv_rel = covid_adv - covid_adv["All industries"]
    tech_occ = pd.Series({s: tech.get(catmap.loc[s, "category"], np.nan) for s in socs})
    tech_occ_ok = tech_occ[[not bool(catmap.loc[s, "volatile_series"]) for s in tech_occ.index]].dropna()
    tech_base = float(tech_occ_ok.median())

    # Centring: every crisis value is published relative to the median of its published values.
    covid_base = float(covid20["value"].reindex(socs).dropna().median())
    gfc_base = float(gfc20["value"].reindex(socs).dropna().median())
    gfc_pay_base = float(gfc_pay20.reindex(socs).dropna().median())
    col_base = float(col_raw.reindex(socs).dropna().median())

    # ---------------- Young workers (APS 2016, includes self-employed) ----------------
    aps = pd.read_excel(raw / "ons_age_bands" / "4digitoccupationand4digitindustrybyagebandsfinal.xls", sheet_name="OCCUPATION", header=None)
    region_row = aps.iloc[6].astype(str).str.strip()
    starts = [c for c in range(aps.shape[1]) if region_row[c] in ("United Kingdom", "UK", "Total")]
    if not starts:
        raise SystemExit(f"APS: no UK block; regions found: {sorted(set(region_row) - {'nan'})}")
    s0 = starts[0]
    ages = aps.iloc[7].astype(str).str.strip()
    total_cols = [c for c in range(s0, min(s0 + 21, aps.shape[1])) if ages[c].lower().startswith(("total", "all"))]
    young_col, total_col = s0 + 2, (total_cols[0] + 2 if total_cols else s0 + 20)
    if not ages[s0].startswith("16"):
        raise SystemExit(f"APS: expected the 16-24 band at column {s0}, found {ages[s0]!r}")
    body = aps.iloc[9:].copy()
    body["code"] = body[1].astype(str).str.extract(r"^(\d{4})")[0]
    body = body.dropna(subset=["code"])

    def apsnum(v):
        s = str(v).strip()
        return 0.0 if s == "-" else pd.to_numeric(s, errors="coerce")

    body["young"] = body[young_col].map(apsnum)
    body["total"] = body[total_col].map(apsnum)
    body = body.drop_duplicates("code").set_index("code")
    share4 = (body.young / body.total).where(body.total > 0)
    okrows = body[body.young.notna() & (body.total > 0)]
    parent_share = okrows.young.groupby(okrows.index.str[:3]).sum() / okrows.total.groupby(okrows.index.str[:3]).sum()
    young10, young_par = share4.copy(), pd.Series(0.0, index=share4.index)
    for code in share4.index:
        if pd.isna(share4[code]) and code[:3] in parent_share.index:
            young10[code], young_par[code] = parent_share[code[:3]], 1.0
    young20, young_par20 = to20(young10), to20(young_par)
    young_zero20 = to20((body.young == 0).astype(float))["value"]

    # ---------------- Demand trends ----------------
    ix_ft, ix_all, ix_grp = year_index(jobs20, CURRENT_YEARS), year_index(jobsall20, CURRENT_YEARS), year_index(gjobs20, CURRENT_YEARS)
    ix_gall = year_index(gjobsall20, CURRENT_YEARS)
    prev_panel = pd.DataFrame({y: clean_jobs(y) for y in PREVIOUS_YEARS})
    ix_prev = year_index(prev_panel, PREVIOUS_YEARS)
    typical_now = theil(CURRENT_YEARS, list(np.exp(ix_ft.values)), min_points=4)
    typical_prev = theil(PREVIOUS_YEARS, list(np.exp(ix_prev.values)), min_points=6)

    # ---------------- Occupations ----------------
    occupations = []
    for soc in socs:
        r = now.loc[soc]
        m = {}
        pur_s, dom = float(purity.get(soc, 1.0)), float(dominant10.get(soc, 0.0))
        conf, cvflags = cv_conf(r["median_cv"])
        base_flags = ["employees_only"] + (["provisional"] if 2025 in provisional_years else [])
        pay_note = "Median gross annual pay of full-time adult employees who have been in the job for over a year, tax year 2024/25. It is not starting pay. Range: 25th to 75th percentile (the middle half)."
        if pd.notna(r["median"]):
            m["pay_median"] = metric(r["median"], "GBP/year", 2025, "ons_ashe_t14", pay_note, low=r["p25"], high=r["p75"], confidence=conf,
                                     flags=base_flags + cvflags, nd=0)
        elif soc[:3] in gnow.index and pd.notna(gnow.loc[soc[:3], "median"]):
            g = gnow.loc[soc[:3]]
            m["pay_median"] = metric(g["median"], "GBP/year", 2025, "ons_ashe_t14",
                                     f"Median full-time pay for the wider group '{g['title']}' (this occupation's own figure is withheld). {pay_note.split('. ', 1)[1]}",
                                     low=g["p25"], high=g["p75"], granularity="parent_group", confidence="low", flags=base_flags + ["imputed_parent"], nd=0)
        else:
            m["pay_median"] = metric(None, "GBP/year", 2025, "ons_ashe_t14", "Median pay is withheld for this occupation and its group.", flags=base_flags)
        for key, c, label in (("pay_p10", "p10", "10th percentile (a floor)"), ("pay_p90", "p90", "90th percentile (a ceiling; rarely published for single occupations)")):
            v = r[c]
            if pd.notna(v):
                pconf, pflags = cv_conf(r.get(f"{c}_cv"))
                m[key] = metric(v, "GBP/year", 2025, "ons_ashe_t14", f"{label} of gross annual pay, full-time adult employees, tax year 2024/25.",
                                confidence=pconf, flags=base_flags + pflags, nd=0)
            elif soc[:3] in gnow.index and pd.notna(gnow.loc[soc[:3], c]):
                g = gnow.loc[soc[:3]]
                m[key] = metric(g[c], "GBP/year", 2025, "ons_ashe_t14", f"{label} for the wider group '{g['title']}' (this occupation's own figure is withheld).",
                                granularity="parent_group", confidence="low", flags=base_flags + ["imputed_parent"], nd=0)
            else:
                m[key] = metric(None, "GBP/year", 2025, "ons_ashe_t14", f"{label}: withheld for this occupation and its group.", flags=base_flags)

        # Real pay change 2015 -> 2025, with a range from sampling error and bridging error.
        rp15, rp25 = real_pay[2015].get(soc, np.nan), real_pay[2025].get(soc, np.nan)
        cov15 = float(paycov_by_year[2015].get(soc, 0.0))
        rflags = ["bridged_soc2010"] + base_flags
        if pur_s < PURITY_MIN:
            rflags.append("bridged_low_purity")
        if cov15 < COVERAGE_MIN:
            rflags.append("partial_sources")
        native = rel_change(pd.Series([real_pay[2025].get(soc, np.nan)]), pd.Series([real_pay[2022].get(soc, np.nan)])).iloc[0]
        if pd.notna(rp15) and pd.notna(rp25):
            L = math.log(rp25 / rp15)
            se15 = float(to20(col(cv10, 2015) / 100)["value"].get(soc, np.nan))
            se25 = float(r["median_cv"]) / 100 if pd.notna(r["median_cv"]) else 0.10
            se15 = se15 if not math.isnan(se15) else 0.10
            bsd = BRIDGE_SD_LOW_PURITY if pur_s < PURITY_MIN else BRIDGE_SD
            h = 1.645 * math.sqrt(se15 ** 2 + se25 ** 2 + bsd ** 2)
            rconf = "medium" if h <= 0.15 else "low"
            if abs(math.expm1(L)) > 0.30:
                rconf = "low"
            m["real_pay_change_10y"] = metric(math.expm1(L), "fraction", "2015-2025", "ons_ashe_t14",
                                              "Real change in median full-time pay, tax year 2014/15 to 2024/25, in 2024/25 prices (CPIH, tax-year average). Range: 90% interval from sampling and code-bridging error.",
                                              low=math.expm1(L - h), high=math.expm1(L + h), confidence=rconf, flags=rflags,
                                              extra={"purity": num(pur_s, 3), "source_coverage_2015": num(cov15, 3),
                                                     "native_real_change_2022_2025": num(math.expm1(native)) if pd.notna(native) else None})
        else:
            m["real_pay_change_10y"] = metric(None, "fraction", "2015-2025", "ons_ashe_t14", "Real pay change can't be computed: pay is withheld in 2015 or 2025.",
                                              flags=rflags, extra={"purity": num(pur_s, 3)})

        jconf, jflags = cv_conf(r.get("jobs_k_cv"))
        m["jobs"] = metric(r["jobs_k"], "thousand jobs", 2025, "ons_ashe_t14",
                           "Full-time employee jobs (ASHE, rounded to the thousand). ONS calls these counts indicative, not accurate estimates.",
                           confidence=jconf, flags=base_flags + jflags + ["ons_indicative_counts"], nd=1)

        # Current demand trend, 2022-2025, against the typical occupation; fallback chain FT -> all -> group.
        t, gran, tflags, tnote = None, "occupation", [], "full-time employee jobs"
        for panel, cvp, ix, key, g, f, n in ((jobs20, jobscv20, ix_ft, soc, "occupation", [], "full-time employee jobs"),
                                             (jobsall20, jobsallcv20, ix_all, soc, "occupation", ["fallback_all_employees"], "all employee jobs (full- and part-time)"),
                                             (gjobs20, gjobscv20, ix_grp, soc[:3], "parent_group", ["imputed_parent"], "full-time jobs in the wider occupation group"),
                                             (gjobsall20, gjobsallcv20, ix_gall, soc[:3], "parent_group", ["imputed_parent", "fallback_all_employees"],
                                              "all employee jobs in the wider occupation group")):
            if key in panel.index:
                t = relative_trend([panel.loc[key].get(y, np.nan) for y in CURRENT_YEARS], CURRENT_YEARS, ix,
                                   [cvp.loc[key].get(y, np.nan) if key in cvp.index else np.nan for y in CURRENT_YEARS], min_points=4)
                if t:
                    gran, tflags, tnote = g, f, n
                    break
        dflags = base_flags + ["ons_indicative_counts"] + tflags
        m["demand_trend"] = metric(t["value"] if t else None, "fraction/year", "2022-2025", "ons_ashe_t14",
                                   f"Yearly change in {tnote} compared with the typical occupation, 2022 to 2025 (+0.02 = growing 2% a year faster). Robust (Theil-Sen) trend; range is a 90% interval including ONS sampling error.",
                                   low=t["low"] if t else None, high=t["high"] if t else None, granularity=gran,
                                   confidence=trend_confidence(t) if t else "low", flags=dflags,
                                   extra={"absolute_trend": num(t["absolute"]) if t and t["absolute"] is not None else None,
                                          "typical_occupation_trend": num(typical_now[0]) if typical_now else None})

        # Previous era, 2011-2019, bridged; points with poor source coverage are blanked.
        t0, n0, f0 = None, "full-time employee jobs", []
        covs = [float(jobscov_by_year[y].get(soc, 0.0)) for y in PREVIOUS_YEARS]
        t0 = relative_trend([clean_jobs(y).get(soc, np.nan) for y in PREVIOUS_YEARS], PREVIOUS_YEARS, ix_prev,
                            [float(to20(col(jobscv10, y))["value"].get(soc, np.nan)) for y in PREVIOUS_YEARS], min_points=6)
        pflags = ["bridged_soc2010", "employees_only", "ons_indicative_counts"] + f0
        if pur_s < PURITY_MIN:
            pflags.append("bridged_low_purity")
        if t0 and (max(covs) - min(covs) > 0.10 or min(covs) < COVERAGE_MIN):
            pflags.append("partial_sources")
        m["demand_trend_2011_19"] = metric(t0["value"] if t0 else None, "fraction/year", "2011-2019", "ons_ashe_t14",
                                           f"Yearly change in {n0} compared with the typical occupation in the previous code era, bridged to today's code. Describes the past; it doesn't predict the future.",
                                           low=t0["low"] if t0 else None, high=t0["high"] if t0 else None,
                                           confidence=trend_confidence(t0) if t0 else "low", flags=pflags,
                                           extra={"absolute_trend": num(t0["absolute"]) if t0 and t0["absolute"] is not None else None,
                                                  "typical_occupation_trend": num(typical_prev[0]) if typical_prev else None, "purity": num(pur_s, 3)})

        e = expo.get(soc)
        if e:
            low, high = max(0.0, e["mean"] - e["half"]), min(1.0, e["mean"] + e["half"])
            flags = (["multi_isco"] if e["n_isco"] > 1 else []) + (["partial_sources"] if e["coverage"] < COVERAGE_MIN else [])
            dp, ip = dfe_pct.get(soc, np.nan), ilo_pct.get(soc, np.nan)
            extra = {"gradient": e["gradient"], "dominant_isco": e["dominant_isco"], "n_isco": e["n_isco"],
                     "ilo_percentile": num(ip, 3), "dfe_percentile": num(dp, 3), "spread_between_codes": num(e["between"], 3),
                     "spread_within_tasks": num(e["within"], 3), "scored_title_share": num(e["coverage"], 3)}
            if pd.notna(dp) and pd.notna(ip) and abs(ip - dp) > 0.30:
                on_ilo = float(np.quantile(ilo_vals.values, dp))
                low, high = min(low, on_ilo), max(high, on_ilo)
                flags.append("sources_disagree")
            econf = "high" if e["half"] <= 0.08 else "medium" if e["half"] <= 0.15 else "low"
            m["exposure"] = metric(e["mean"], "score 0-1", 2025, "ilo_wp140",
                                   "Generative-AI exposure of the job's tasks (ILO 2025), averaged over the international codes its UK job titles map to. Range: how much exposure varies across its tasks and codes, widened where the UK (DfE) estimate disagrees.",
                                   low=low, high=high, confidence=econf, flags=flags, extra=extra)
        else:
            m["exposure"] = metric(None, "score 0-1", 2025, "ilo_wp140",
                                   "Missing: fewer than half of this occupation's UK job titles map to an occupation the ILO scored.",
                                   extra={"scored_title_share": num(float(expo_cov.get(soc, 0.0)), 3)})
        dpv = dfe_pct.get(soc, np.nan)
        m["exposure_uk"] = metric(dpv, "score 0-1", 2023, "dfe_ai_uk_2023",
                                  "Percentile rank of the DfE's language-model exposure score among UK occupations (1 = most exposed). A cross-check, not a second headline number.",
                                  confidence="medium", flags=["bridged_soc2010"])

        cat = catmap.loc[soc, "category"]
        volatile = bool(catmap.loc[soc, "volatile_series"])
        cv_ = covid20["value"].get(soc, np.nan)
        par = float(covid_par20["value"].get(soc, 0.0)) if soc in covid_par20.index else 0.0
        cval = cv_ - covid_base if pd.notna(cv_) else np.nan
        cflags = ["covid_year", "bridged_soc2010", "employees_only"] + (["imputed_parent"] if par > 0.10 else [])
        if pur_s < PURITY_MIN:
            cflags.append("bridged_low_purity")
        m["resilience_covid"] = metric(math.expm1(cval) if pd.notna(cval) else None, "fraction", "2019-2020", "ons_ashe_t14",
                                       "Change in employee jobs from 2019 to 2020 compared with the typical occupation (+0.10 = about 10% better). Own figure only for jobs with at least 50,000 employees, else the wider group.",
                                       granularity="parent_group" if par > 0.5 else "occupation",
                                       confidence="low" if (pd.isna(cval) or abs(cval) > 0.4) else "medium", flags=cflags,
                                       extra={"adverts_category": cat, "adverts_vs_all_2020": num(math.expm1(covid_adv_rel.get(cat, np.nan))),
                                              "parent_share": num(par, 3)})

        c4 = col_raw.get(soc, np.nan)
        cpar = float(col_par.get(soc, 0.0)) if soc in col_par.index else 0.0
        clv = c4 - col_base if pd.notna(c4) else np.nan
        m["resilience_cost_of_living"] = metric(math.expm1(clv) if pd.notna(clv) else None, "fraction", "2023-2025", "ons_ashe_t14",
                                                "Real pay change after the cost-of-living shock, tax year 2022/23 (peak inflation) to 2024/25, compared with the typical occupation (+0.05 = about 5% better). Own median only when ONS's sampling error is at most 10%, else the wider group.",
                                                granularity="parent_group" if cpar > 0.5 else "occupation",
                                                confidence="low" if (pd.isna(clv) or abs(clv) > 0.3) else "medium",
                                                flags=["employees_only"] + (["imputed_parent"] if cpar > 0.10 else []),
                                                extra={"parent_share": num(cpar, 3)})

        tv = tech.get(cat, np.nan) - tech_base if not volatile else np.nan
        m["resilience_tech_slump"] = metric(math.expm1(tv) if pd.notna(tv) else None, "fraction", "2022-2024", "ons_online_job_adverts",
                                            (VOLATILE_NOTE if volatile else
                                             f"Change in online job adverts for the '{cat}' category, January-June 2022 to January-June 2024, compared with the typical occupation's category (de-duplicated adverts)."),
                                            granularity="estimate", confidence="low", flags=["category_level"], extra={"adverts_category": cat, "volatile_category": volatile})

        gv = gfc20["value"].get(soc, np.nan)
        gpar = float(gfc_par20["value"].get(soc, 0.0)) if soc in gfc_par20.index else 0.0
        gval = gv - gfc_base if pd.notna(gv) else np.nan
        gp = gfc_pay20.get(soc, np.nan)
        m["resilience_2008"] = metric(math.expm1(gval) if pd.notna(gval) else None, "fraction", "2008-2009", "ons_ashe_t14",
                                      "Change in employee jobs from 2008 to 2009 compared with the typical occupation, measured in the old SOC 2000 codes. Not for cards: in a placebo test the 2008-09 spread between careers was no larger than in ordinary years.",
                                      granularity="parent_group" if gpar > 0.5 else "occupation", confidence="low",
                                      flags=["bridged_soc2000", "bridged_soc2010", "employees_only"] + (["imputed_parent"] if gpar > 0.10 else []),
                                      extra={"real_pay_vs_typical": num(math.expm1(gp - gfc_pay_base)) if pd.notna(gp) else None,
                                             "parent_share": num(gpar, 3), "show_on_card": pl_gfc["passes"]})

        yv = young20["value"].get(soc, np.nan)
        ypar = float(young_par20["value"].get(soc, 0.0)) if soc in young_par20.index else 0.0
        yzero = float(young_zero20.get(soc, 0.0)) > 0.5
        yflags = ["bridged_soc2010"] + (["imputed_parent"] if ypar > 0.10 else [])
        if pur_s < PURITY_MIN:
            yflags.append("bridged_low_purity")
        m["young_worker_share"] = metric(yv, "fraction", 2016, "ons_aps_2016_age",
                                         "Share of people in this job aged 16 to 24 in 2016, including self-employed: a sign of how open it is to young entrants. Survey estimate from small samples.",
                                         granularity="parent_group" if ypar > 0.5 else "occupation",
                                         confidence="low" if (pd.isna(yv) or yzero) else "medium", flags=yflags)
        occupations.append({"soc2020": soc, "title": titles.get(soc, soc), "short_title": DEMO.get(soc, titles.get(soc, soc)),
                            "isco08": [{"code": c, "share": round(float(s), 4)} for c, s in
                                       isco[isco.soc2020 == soc].sort_values("share", ascending=False)[["isco08", "share"]].itertuples(index=False)],
                            "in_demo_set": soc in DEMO, "metrics": m})
    occ_by_soc = {o["soc2020"]: o for o in occupations}

    # ---------------- Hedges ----------------
    cand = json.loads((proc / "hedges_candidates.json").read_text(encoding="utf-8"))
    hedges = {}
    for soc in socs:
        ex_a = occ_by_soc[soc]["metrics"]["exposure"]["value"]
        items = []
        for c in cand.get(soc, {"candidates": []})["candidates"]:
            ex_b = occ_by_soc.get(c["soc2020"], {}).get("metrics", {}).get("exposure", {}).get("value")
            delta = (ex_b - ex_a) if (ex_a is not None and ex_b is not None) else None
            items.append({"soc2020": c["soc2020"], "title": titles.get(c["soc2020"], c["soc2020"]), "similarity": c["similarity"],
                          "shared_skills": c["shared_skills"], "evidence": c["evidence"], "status": "preliminary",
                          "exposure_delta": num(delta, 3), "lower_exposure": bool(delta is not None and delta <= -0.05),
                          "why": f"Shares {c['n_shared']} skills, e.g. {', '.join(c['shared_skills'][:3])}"
                                 + ("; estimate from few job-title links" if c["evidence"] == "estimate" else "")})
        hedges[soc] = items

    # ---------------- Backtest ----------------
    windows, spear = [], {}
    dom_src = comp.sort_values("weight", ascending=False).drop_duplicates("soc2020").set_index("soc2020")["soc2010"]

    def stat(values):
        v = boot(values)
        return {"median": num(math.expm1(v[0])), "low": num(math.expm1(v[1])), "high": num(math.expm1(v[2]))} if v[0] is not None else None

    for base in (2013, 2014, 2015):
        end = base + 5
        full = pd.DataFrame({"pay": col(pay10, base), "prior": rel_change(col(jobs10, base), col(jobs10, 2011))}).dropna()
        d = full.join(pd.DataFrame({"pay_end": col(pay10, end), "rpg": rel_change(col(pay10, end) / cpi[end], col(pay10, base) / cpi[base]),
                                    "jg": rel_change(col(jobs10, end), col(jobs10, base))}), how="inner").dropna()
        tiers = assign_tiers(full)
        amb, safe = tiers.ambitious.reindex(d.index), tiers.safe.reindex(d.index)
        top_end = d.pay_end >= d.pay_end.quantile(2 / 3)
        spear[str(base)] = {"pay_level_vs_later_real_pay_growth": round(float(d[["pay", "rpg"]].corr("spearman").iloc[0, 1]), 3),
                            "prior_jobs_growth_vs_later_jobs_growth": round(float(d[["prior", "jg"]].corr("spearman").iloc[0, 1]), 3)}

        def group(key, label, mask):
            if mask is None:
                return {"key": key, "label": label, "n": 0, "real_pay_growth": None, "jobs_growth": None, "share_jobs_fell": None}
            return {"key": key, "label": label, "n": int(mask.sum()), "real_pay_growth": stat(d[mask].rpg), "jobs_growth": stat(d[mask].jg),
                    "share_jobs_fell": num(float((d[mask].jg < 0).mean()))}
        rows = []
        for soc in socs:
            src = dom_src.get(soc)
            if src in d.index:
                ing = [k for k, msk in (("ambitious", amb), ("safe", safe)) if msk[src]]
                rows.append({"soc2020": soc, "group_then": ing[0] if ing else "other", "in_groups": ing,
                             "real_pay_growth": num(math.expm1(d.loc[src, "rpg"])), "jobs_growth": num(math.expm1(d.loc[src, "jg"])), "flags": ["bridged_soc2010"]})
        wflags = (["provisional"] if end in provisional_years else []) + (["covid_year"] if end == 2020 else [])
        windows.append({"base_year": base, "outcome_year": end, "horizon": 5, "coding": "SOC 2010 native", "flags": wflags, "jobs_comparable": True,
                        "n_base_occupations": int(len(full)), "n_scored": int(len(d)),
                        "persistence": {"pay_rank_spearman": round(float(d[["pay", "pay_end"]].corr("spearman").iloc[0, 1]), 3),
                                        "top_third_by_pay_still_top_third": num(float(top_end[amb].mean()), 3)},
                        "groups": [group("ambitious", "Top third by pay then", amb), group("balanced", "No simple-rule version", None),
                                   group("safe", "Top third by jobs growth since 2011 then", safe), group("all", "All occupations with complete data", d.pay.notna())],
                        "occupations": rows})
    sp = pd.DataFrame({y: real_pay[y] for y in real_pay})
    sj = pd.DataFrame({y: clean_jobs(y) for y in range(2011, 2021)})
    full = pd.DataFrame({"pay": sp[2019], "prior": rel_change(sj[2019], sj[2015])}).dropna()
    d = full.join(pd.DataFrame({"pay_end": sp[2024], "rpg": rel_change(sp[2024], sp[2019])}), how="inner").dropna()
    tiers = assign_tiers(full)
    amb, safe = tiers.ambitious.reindex(d.index), tiers.safe.reindex(d.index)
    top_end = d.pay_end >= d.pay_end.quantile(2 / 3)

    def pay_group(key, label, mask):
        if mask is None:
            return {"key": key, "label": label, "n": 0, "real_pay_growth": None, "jobs_growth": None, "share_jobs_fell": None}
        return {"key": key, "label": label, "n": int(mask.sum()), "real_pay_growth": stat(d[mask].rpg), "jobs_growth": None, "share_jobs_fell": None}
    windows.append({"base_year": 2019, "outcome_year": 2024, "horizon": 5, "coding": "bridged SOC 2010 -> SOC 2020", "flags": ["bridged_soc2010", "covid_year", "recoded_2021"],
                    "jobs_comparable": False, "n_base_occupations": int(len(full)), "n_scored": int(len(d)),
                    "persistence": {"pay_rank_spearman": round(float(d[["pay", "pay_end"]].corr("spearman").iloc[0, 1]), 3),
                                    "top_third_by_pay_still_top_third": num(float(top_end[amb].mean()), 3)},
                    "groups": [pay_group("ambitious", "Top third by pay then", amb), pay_group("balanced", "No simple-rule version", None),
                               pay_group("safe", "Top third by jobs growth 2015-19 then", safe), pay_group("all", "All occupations with complete data", d.pay.notna())],
                    "occupations": [{"soc2020": s, "group_then": ("ambitious" if amb[s] else "safe" if safe[s] else "other"),
                                     "in_groups": [k for k, msk in (("ambitious", amb), ("safe", safe)) if msk[s]],
                                     "real_pay_growth": num(math.expm1(d.loc[s, "rpg"])), "jobs_growth": None, "flags": ["bridged_soc2010", "covid_year"]}
                                    for s in socs if s in d.index]})

    # ---------------- Evaluation (this script's checks only; others are merged, not replaced) ----------------
    def seam(bridged_pay, native_pay, bridged_jobs, native_jobs):
        out = {}
        for name, b, n in (("pay", bridged_pay, native_pay), ("jobs", bridged_jobs, native_jobs)):
            r = (n / b).replace([np.inf, -np.inf], np.nan).dropna()
            err = np.log(r) - float(np.log(r).median())
            out[name] = {"n": int(len(r)), "median_ratio": num(r.median(), 3), "iqr": [num(r.quantile(.25), 3), num(r.quantile(.75), 3)],
                         "share_outside_0.8_1.25": num(float(((r < 0.8) | (r > 1.25)).mean()), 3),
                         "abs_error_net_of_median": {"median": num(err.abs().median(), 3), "p90": num(err.abs().quantile(0.9), 3)}}
        return out
    seam_pay = (np.log(col(pay20, 2021) / pay_by_year[2020]) - float(np.log(col(pay20, 2021) / pay_by_year[2020]).median())).abs().dropna()
    by_purity = {lab: {"n": int(len(v)), "median_abs_error": num(v.median(), 3), "p90_abs_error": num(v.quantile(0.9), 3)}
                 for lab, v in (("purity_below_0.5", seam_pay[purity.reindex(seam_pay.index) < 0.5]),
                                ("purity_0.5_to_0.95", seam_pay[(purity.reindex(seam_pay.index) >= 0.5) & (purity.reindex(seam_pay.index) < 0.95)]),
                                ("purity_0.95_plus", seam_pay[purity.reindex(seam_pay.index) >= 0.95]))}
    split0 = pd.read_csv(proc / "soc2000_to_soc2010.csv", dtype={"soc2000": str, "soc2010": str})
    j0 = split0.merge(col(jobsall00, 2010).rename("v").rename_axis("soc2000").reset_index(), on="soc2000").dropna(subset=["v"])
    hv = pd.read_csv(proc / "hedge_validation.csv", dtype={"soc2020": str})
    matched = hv.dropna(subset=["same_minor_group"])
    diffs = (matched.hit_at_3 - matched.same_minor_group).values
    rng = np.random.default_rng(0)
    draws = [diffs[rng.integers(0, len(diffs), len(diffs))].mean() for _ in range(2000)]
    hits = hv.hit_at_3.values
    hit_draws = [hits[rng.integers(0, len(hits), len(hits))].mean() for _ in range(2000)]
    demo_dis = [{"soc2020": s, "ilo_percentile": num(ilo_pct.get(s), 3), "dfe_percentile": num(dfe_pct.get(s), 3)}
                for s in DEMO if pd.notna(dfe_pct.get(s)) and pd.notna(ilo_pct.get(s)) and abs(ilo_pct[s] - dfe_pct[s]) > 0.30]
    checks = {
        "bridge_seam": {"status": "preliminary", "date": NOW[:10],
                        "summary": "Bridged vs native values at both code changes. Pay lines up on average (per-occupation error about 4%, larger where purity is low); job counts don't.",
                        "metrics": {"2020_2021": seam(pay_by_year[2020], col(pay20, 2021), jobs_by_year[2020], col(jobs20, 2021)),
                                    "2010_2011_all_employees": seam(to10(col(piv(ALL, 2000, "median"), 2010))["value"], col(piv(ALL, 2010, "median"), 2011),
                                                                    (j0.share * j0.v).groupby(j0.soc2010).sum(), col(jobsall10, 2011)),
                                    "pay_seam_by_purity": by_purity, "n_low_purity": int((purity.reindex(socs) < PURITY_MIN).sum())}},
        "backtest_probe": {"status": "preliminary", "date": NOW[:10], "summary": "Spearman correlations in the native windows (simple rules, not the app's picks).", "metrics": spear},
        "exposure_agreement": {"status": "preliminary", "date": NOW[:10],
                               "summary": "ILO (weighted) vs DfE language-model exposure: rank correlation across all occupations and within 2-digit groups. Both are task-based methods, so this is agreement between two methods, not proof.",
                               "metrics": {"spearman": round(rho, 3), "spearman_within_2digit_groups": round(rho_within2, 3), "n": int(len(both)),
                                           "demo_disagreements_over_30_points": demo_dis}},
        "hedge_sanity": {"status": "preliminary", "date": NOW[:10],
                         "summary": f"Share of top-3 hedges that O*NET (US) also lists as related, for the {len(hv)} of {len(socs)} occupations with title-based links. Compared on the same occupations, hedges beat 'any job in the same 3-digit group' by a few points. The reference goes through the same SOC-to-ESCO links, so it is partly circular.",
                         "metrics": {"n": int(len(hv)), "n_occupations": len(socs), "hit_at_3": num(hits.mean(), 3),
                                     "hit_at_3_ci95": [num(np.percentile(hit_draws, 2.5), 3), num(np.percentile(hit_draws, 97.5), 3)],
                                     "baseline_random_same_level": num(hv.random_same_level.mean(), 3),
                                     "matched_n": int(len(matched)), "matched_hit_at_3": num(matched.hit_at_3.mean(), 3),
                                     "matched_baseline_same_3_digit_group": num(matched.same_minor_group.mean(), 3),
                                     "matched_difference": num(diffs.mean(), 3),
                                     "matched_difference_ci95": [num(np.percentile(draws, 2.5), 3), num(np.percentile(draws, 97.5), 3)],
                                     "demo_hit_at_3": num(hv[hv.soc2020.isin(list(DEMO))].hit_at_3.mean(), 3),
                                     "demo_zero_hits": hv[hv.soc2020.isin(list(DEMO)) & (hv.hit_at_3 == 0)].soc2020.tolist()}},
        "crisis_placebo": {"status": "preliminary", "date": NOW[:10],
                           "summary": "Does each crisis show more spread between careers than ordinary years? Crises that fail are kept in the files but not shown on cards.",
                           "metrics": {"covid": pl_covid, "gfc_2008": pl_gfc, "cost_of_living": pl_col,
                                       "tech_slump": {"passes": None, "note": "Not testable: the advert series starts in 2018, so there are no ordinary two-year windows."}}},
    }

    crises = [
        {"key": "covid", "label": "COVID-19", "window": "2019-2020", "measure": "Employee jobs (all), relative to the median occupation",
         "baseline_median": num(math.expm1(covid_base)), "status": "preliminary", "flags": ["covid_year", "bridged_soc2010"],
         "show_on_card": pl_covid["passes"], "placebo": pl_covid},
        {"key": "cost_of_living", "label": "After the cost-of-living shock", "window": "2023-2025",
         "measure": "Real median full-time pay, tax year 2022/23 (peak inflation) to 2024/25, relative to the median occupation",
         "baseline_median": num(math.expm1(col_base)), "status": "preliminary", "flags": [], "show_on_card": pl_col["passes"], "placebo": pl_col},
        {"key": "tech_slump", "label": "Hiring slump", "window": "2022-2024",
         "measure": "Online job adverts by category (de-duplicated), January-June 2022 to January-June 2024, relative to the median occupation's category",
         "baseline_median": num(math.expm1(tech_base)), "baseline_all_adverts": num(math.expm1(tech["All industries"])), "status": "preliminary",
         "flags": ["category_level"], "show_on_card": True, "placebo": checks["crisis_placebo"]["metrics"]["tech_slump"]},
        {"key": "gfc_2008", "label": "2008 financial crisis", "window": "2008-2009", "measure": "Employee jobs (all), SOC 2000, relative to the median occupation",
         "baseline_median": num(math.expm1(gfc_base)), "baseline_real_pay_median": num(math.expm1(gfc_pay_base)),
         "status": "preliminary", "flags": ["bridged_soc2000", "bridged_soc2010"], "show_on_card": pl_gfc["passes"], "placebo": pl_gfc},
    ]

    meta = {"schema_version": SCHEMA_VERSION, "generated_at": NOW}
    placeholder_fit = {**meta, "status": "mock", "method": "hand-assigned placeholder affinities until the matcher is evaluated",
                       "tags": [{"id": t, "label": lbl, "keywords": kws} for t, lbl, kws in TAGS], "affinity": AFFINITY}
    method = ("Simple rules, not the app's picks. Ambitious: top third by pay at the base year. Safe: top third by jobs growth before the base year. "
              "Outcomes 5 years later; real pay deflated by tax-year CPIH. The rules were fixed before these windows were scored, but earlier probes had looked at 2013-2019.")
    caveats = ["These are simple rules, not the app's Ambitious, Balanced and Safe picks; there is no simple-rule version of Balanced.",
               "Historical tiers use market data only: no historical AI exposure index exists.",
               "Windows overlap, so they are not independent.",
               "Only occupations with data at both ends are scored (larger occupations); n_base_occupations and n_scored say how many dropped out.",
               "Low-pay occupations gained from minimum-wage rises after 2016, which lowers the Ambitious group's relative pay growth. Pay level itself persists strongly (see persistence).",
               "Windows crossing 2021 compare pay only; job counts are not comparable across the code change.",
               "Windows ending in 2020 include the COVID year; 2018 is a provisional ONS edition."]
    mock_set = set(DEMO) | {h["soc2020"] for s in DEMO for h in hedges.get(s, [])}
    for out_dir, subset in ((snap, None), (snap / "mock", mock_set)):
        keep = (lambda s: True) if subset is None else (lambda s: s in subset)
        write(out_dir, "occupations", {**meta, "status": "preliminary", "price_base": "CPIH, tax year 2024/25 average", "demo_set": list(DEMO),
                                       "occupations": [o for o in occupations if keep(o["soc2020"])]})
        write(out_dir, "history", {**meta, "status": "preliminary", "occupations": {k: v for k, v in history.items() if keep(k)}})
        write(out_dir, "hedges", {**meta, "status": "preliminary", "method": "esco_skill_jaccard: ESCO skill overlap (IDF-weighted Jaccard), same ONS skill level; checked against O*NET",
                                  "occupations": {k: [h for h in v if keep(h["soc2020"])] for k, v in hedges.items() if keep(k)}})
        current_fit = load_json(out_dir / "fit.json")
        if current_fit is None or current_fit.get("status") == "mock":
            real_fit = load_json(snap / "fit.json")
            write(out_dir, "fit", real_fit if (subset is not None and real_fit and real_fit.get("status") != "mock") else placeholder_fit)
        write(out_dir, "backtest", {**meta, "status": "preliminary", "method": method, "caveats": caveats,
                                    "windows": [{**w, "occupations": [o for o in w["occupations"] if keep(o["soc2020"])]} for w in windows]})
        write(out_dir, "crises", {**meta, "status": "preliminary", "crises": crises})
        write(out_dir, "sources", {**meta, "status": "preliminary", "sources": SOURCES})
        old_eval = load_json(out_dir / "eval.json") or {}
        merged = dict(old_eval.get("checks", {}))
        for k, v in checks.items():
            if k == "exposure_agreement" and "inhouse" in merged.get(k, {}).get("metrics", {}):
                v = {**v, "metrics": {**v["metrics"], "inhouse": merged[k]["metrics"]["inhouse"]}}
            merged[k] = v
        merged.setdefault("matcher", {"status": "pending", "date": NOW[:10], "summary": "Matcher not evaluated yet (run m1_matcher.py).", "metrics": {}})
        write(out_dir, "eval", {**meta, "status": "preliminary", "checks": merged})
    print(f"occupations: {len(occupations)}; mock set: {len(mock_set)}; hedges for {sum(bool(v) for v in hedges.values())}; windows: {len(windows)}; "
          f"exposure spearman {rho:.2f} (within 2-digit {rho_within2:.2f}, n={len(both)}); low purity: {int((purity.reindex(socs) < PURITY_MIN).sum())}")
    for k, p in (("covid", pl_covid), ("gfc_2008", pl_gfc), ("cost_of_living", pl_col)):
        print(f"placebo {k}: ratio {p['ratio']} -> {'show' if p['passes'] else 'hide'} (window {p['window_robust_sd']}, ordinary {p['ordinary_robust_sd_median']})")


if __name__ == "__main__":
    main()
