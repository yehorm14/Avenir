"""Build the ML artefacts (contract v1.1) for every SOC 2020 occupation, plus the demo-set mocks.

Usage: python -I build_artefacts.py RAW_DIR PROCESSED_DIR SNAPSHOT_DIR

Writes SNAPSHOT_DIR/*.json (all occupations) and SNAPSHOT_DIR/mock/*.json (the 20 demo
careers, same shapes). Inputs come from the other scripts: ashe_parse, crosswalk_build,
crosswalk_2000, ilo_parse, esco_link, hedges_build, validate_hedges.

Rules agreed with the team (docs/decisions.md):
- Fallback chain for sparse occupations: full-time counts -> all-employee counts ->
  the ONS 3-digit parent group, each step flagged ("imputed_parent" for the parent).
- Job counts never cross a code change: trends stay inside one coding era; crisis
  windows are measured natively (COVID in SOC 2010, 2008 in SOC 2000) and only the
  relative change is carried to today's codes.
- Pay bridges cleanly (tested at both seams), so the real pay path runs 2007-2025.
- Exposure: ILO weighted over mapped ISCO codes; DfE as a percentile cross-check;
  disagreement widens the range and adds "sources_disagree".
- Tech slump: ONS online job adverts are category level only ("category_level").
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from ml_common import (AFFINITY, DEMO, NOW, SCHEMA_VERSION, SOURCES, TAGS, boot, cpih_april,  # noqa: E402
                       cv_conf, metric, num, theil, trend_conf, weighted_map, write)

MIN_JOBS_K = 20  # below this, 4-digit counts are too coarse (rounded to the thousand)
CRISIS_MIN_JOBS_K = 50  # crisis job-count changes use the occupation's own figure only above this (agreed 17 Oct)
MAX_PAY_CV = 10  # pay-based crisis values use the occupation's own median only when ONS's CV is at most this

# Longest-prefix map from SOC 2020 to the ONS/Adzuna advert categories (hand-made; flagged).
CATEGORY_RULES = {
    "11": "Management / exec / consulting", "12": "Management / exec / consulting", "122": "Catering and hospitality",
    "124": "Healthcare and Social care", "211": "Scientific / QA", "212": "Engineering", "213": "IT / Computing / Software",
    "214": "Creative / design / arts & media", "215": "Scientific / QA", "22": "Healthcare and Social care", "23": "Education",
    "241": "Legal", "242": "Accounting / Finance", "243": "Accounting / Finance", "244": "Healthcare and Social care",
    "245": "Construction / trades", "2454": "Property", "246": "Scientific / QA", "247": "Creative / design / arts & media",
    "31": "Engineering", "313": "IT / Computing / Software", "32": "Healthcare and Social care", "33": "Other / general",
    "34": "Creative / design / arts & media", "344": "Other / general", "351": "Transport / logistics / warehouse", "352": "Legal",
    "353": "Accounting / Finance", "354": "Sales", "3544": "IT / Computing / Software", "3545": "Marketing / advertising / PR",
    "3546": "Marketing / advertising / PR", "355": "Scientific / QA", "356": "HR & recruitment", "357": "HR & recruitment",
    "4": "Admin / clerical / secretarial", "51": "Other / general", "52": "Engineering", "524": "Construction / trades",
    "53": "Construction / trades", "54": "Manufacturing", "543": "Catering and hospitality", "61": "Healthcare and Social care",
    "62": "Travel / tourism", "623": "Facilities / maintenance", "7": "Sales", "71": "Wholesale and retail",
    "72": "Customer service / support", "81": "Manufacturing", "82": "Transport / logistics / warehouse", "91": "Manufacturing",
    "921": "Admin / clerical / secretarial", "923": "Facilities / maintenance", "925": "Transport / logistics / warehouse",
    "926": "Catering and hospitality", "927": "Catering and hospitality",
}


def category_of(soc: str) -> str:
    for n in range(len(soc), 0, -1):
        if soc[:n] in CATEGORY_RULES:
            return CATEGORY_RULES[soc[:n]]
    return "Other / general"


def piv(df, version, col):
    return df[df.soc_version == version].pivot_table(index="soc_code", columns="year", values=col)


def rel_change(new: pd.Series, old: pd.Series) -> pd.Series:
    return np.log(new / old).replace([np.inf, -np.inf], np.nan)


def native_relative(unit_new, unit_old, unit_base, grp_new, grp_old, min_base=CRISIS_MIN_JOBS_K):
    """Log change per 4-digit code, falling back to the ONS 3-digit parent when the base is
    below `min_base` thousand jobs or a value is missing. Returns (relative to the 4-digit median,
    used_parent, baseline)."""
    rel4 = rel_change(unit_new, unit_old)
    baseline = float(rel4.dropna().median())
    grel = rel_change(grp_new, grp_old)
    vals, used = {}, {}
    for code in unit_old.index.union(unit_new.index):
        ok = pd.notna(rel4.get(code)) and pd.notna(unit_base.get(code)) and unit_base.get(code) >= min_base
        if ok:
            vals[code], used[code] = rel4[code] - baseline, 0.0
        elif pd.notna(grel.get(code[:3])):
            vals[code], used[code] = grel[code[:3]] - baseline, 1.0
    return pd.Series(vals, dtype=float), pd.Series(used, dtype=float), baseline


def pay_relative(pay_new, pay_old, cv_new, cv_old, grp_new, grp_old):
    """Real-pay log change per 4-digit code (inputs already deflated), using the occupation's own
    medians only when both CVs are at most MAX_PAY_CV; otherwise the ONS 3-digit parent."""
    rel4 = rel_change(pay_new, pay_old)
    baseline = float(rel4.dropna().median())
    grel = rel_change(grp_new, grp_old)
    vals, used = {}, {}
    for code in pay_old.index.union(pay_new.index):
        ok = pd.notna(rel4.get(code)) and (cv_new.get(code, 99) or 99) <= MAX_PAY_CV and (cv_old.get(code, 99) or 99) <= MAX_PAY_CV
        if ok:
            vals[code], used[code] = rel4[code] - baseline, 0.0
        elif pd.notna(grel.get(code[:3])):
            vals[code], used[code] = grel[code[:3]] - baseline, 1.0
    return pd.Series(vals, dtype=float), pd.Series(used, dtype=float), baseline


def main() -> None:
    raw, proc, snap = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    cpi = cpih_april(raw / "ons_cpih" / "cpih_index_l522.csv")
    a = pd.read_parquet(proc / "ashe_long.parquet")
    grp = pd.read_parquet(proc / "ashe_groups.parquet")
    comp = pd.read_csv(proc / "soc2020_from_soc2010.csv", dtype={"soc2020": str, "soc2010": str})
    split = pd.read_csv(proc / "soc2010_to_soc2020.csv", dtype={"soc2010": str, "soc2020": str})
    comp0 = pd.read_csv(proc / "soc2010_from_soc2000.csv", dtype={"soc2010": str, "soc2000": str})
    ilo = pd.read_csv(proc / "ilo_exposure.csv", dtype={"isco08": str})

    FT, ALL = a[a.sheet == "Full-Time"], a[a.sheet == "All"]
    GFT, GALL = grp[(grp.sheet == "Full-Time") & (grp.level == 3)], grp[(grp.sheet == "All") & (grp.level == 3)]
    pay20, jobs20, jobsall20 = piv(FT, 2020, "median"), piv(FT, 2020, "jobs_k"), piv(ALL, 2020, "jobs_k")
    gpay20, gjobs20 = piv(GFT, 2020, "median"), piv(GFT, 2020, "jobs_k")
    pay10, jobs10, jobsall10, gjobsall10 = piv(FT, 2010, "median"), piv(FT, 2010, "jobs_k"), piv(ALL, 2010, "jobs_k"), piv(GALL, 2010, "jobs_k")
    pay00, jobsall00, gjobsall00 = piv(FT, 2000, "median"), piv(ALL, 2000, "jobs_k"), piv(GALL, 2000, "jobs_k")
    now = FT[FT.year == 2025].set_index("soc_code")
    gnow = GFT[GFT.year == 2025].set_index("soc_code")
    titles = now.title.to_dict()
    socs = sorted(now.index)

    def to20(values10: pd.Series) -> pd.DataFrame:
        return weighted_map(values10.rename_axis("soc2010"), comp, "soc2010", "soc2020")

    def to10(values00: pd.Series) -> pd.DataFrame:
        return weighted_map(values00.rename_axis("soc2000"), comp0, "soc2000", "soc2010")

    def jobs_to20(jobs: pd.Series) -> pd.Series:
        j = split.merge(jobs.rename("v").rename_axis("soc2010").reset_index(), on="soc2010").dropna(subset=["v"])
        return (j.share * j.v).groupby(j.soc2020).sum()

    # ---------------- Real pay path 2007-2025 and bridged jobs 2011-2020 ----------------
    pay_by_year, jobs_by_year = {}, {}
    for y in range(2007, 2011):
        pay_by_year[y] = to20(to10(pay00[y]).value)["value"]
    for y in range(2011, 2021):
        pay_by_year[y] = to20(pay10[y])["value"]
        jobs_by_year[y] = jobs_to20(jobs10[y])
    jobsall_by_year = {y: jobs_to20(jobsall10[y]) for y in range(2011, 2021)}
    for y in range(2021, 2026):
        pay_by_year[y] = pay20[y]
        jobs_by_year[y] = jobs20[y]

    history = {}
    for soc in socs:
        pts = []
        for y in range(2007, 2026):
            p = pay_by_year[y].get(soc, np.nan)
            jk = jobs_by_year.get(y, pd.Series(dtype=float)).get(soc, np.nan) if y >= 2011 else np.nan
            flags = []
            if y <= 2010:
                flags += ["bridged_soc2000", "bridged_soc2010"]
            elif y <= 2020:
                flags.append("bridged_soc2010")
            if y == 2020:
                flags.append("covid_year")
            if y in (2018, 2025):
                flags.append("provisional")
            if y >= 2021:
                flags.append("recoded_2021")
            if pd.isna(p) and pd.isna(jk):
                continue
            pts.append({"year": y, "pay_median": num(p, 0), "pay_median_real": num(p * cpi[2025] / cpi[y], 0) if pd.notna(p) else None,
                        "jobs_k": num(jk, 1), "flags": flags})
        history[soc] = pts
    real_pay = {y: pay_by_year[y] * cpi[2025] / cpi[y] for y in pay_by_year}

    # ---------------- Exposure: ILO weighted, DfE percentile cross-check ----------------
    idx = pd.read_excel(raw / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index", dtype=str,
                        usecols=["SOC_2020", "ISCO-08 code based on SOC2020"])
    idx.columns = ["soc2020", "isco08"]
    idx = idx.dropna()
    idx = idx[idx.soc2020.str.fullmatch(r"\d{4}") & idx.isco08.str.fullmatch(r"\d{4}")]
    isco = idx.groupby(["soc2020", "isco08"]).size().rename("n").reset_index()
    isco["share"] = isco.n / isco.groupby("soc2020").n.transform("sum")
    isco = isco.merge(ilo, on="isco08", how="left")
    expo = {}
    for soc, g in isco.dropna(subset=["exposure_mean"]).groupby("soc2020"):
        w = g.share / g.share.sum()
        mean = float((w * g.exposure_mean).sum())
        sd = float(np.sqrt((w * (g.exposure_mean - mean) ** 2).sum()))
        top = g.loc[g.share.idxmax()]
        expo[soc] = {"mean": mean, "sd": sd, "gradient": top["gradient"], "dominant_isco": top["isco08"], "n_isco": int(len(g)), "imputed": False}
    for soc in socs:
        if soc not in expo:
            sib = [v["mean"] for k, v in expo.items() if k[:3] == soc[:3] and not v["imputed"]]
            if sib:
                expo[soc] = {"mean": float(np.mean(sib)), "sd": float(np.std(sib)), "gradient": None, "dominant_isco": None, "n_isco": 0, "imputed": True}
    ilo_vals = pd.Series({k: v["mean"] for k, v in expo.items()})
    ilo_pct = ilo_vals.rank(pct=True)
    dfe = pd.read_excel(raw / "dfe_ai" / "Annex_1_-_Impact_of_AI_on_UK_jobs_and_training_data_sources.xlsx", sheet_name="AIOE by education level", header=2)
    dfe["soc2010"] = dfe["SOC"].astype(str).str.extract(r"(\d{4})")[0]
    dfe = dfe.dropna(subset=["soc2010", "LLM"]).drop_duplicates("soc2010").set_index("soc2010")["LLM"].astype(float)
    dfe20 = to20(dfe)
    dfe_pct = dfe20["value"].rank(pct=True)
    both = ilo_vals.to_frame("ilo").join(dfe20["value"].rename("dfe"), how="inner").dropna()
    rho = float(spearmanr(both.ilo, both.dfe).statistic)

    # ---------------- Crises ----------------
    covid_rel, covid_parent, covid_base = native_relative(jobsall10[2020], jobsall10[2019], jobsall10[2019], gjobsall10[2020], gjobsall10[2019])
    covid20, covid_par20 = to20(covid_rel), to20(covid_parent)
    # 2008: April 2008 -> April 2009 (the trough in ASHE timing), in native SOC 2000. Headline is the
    # worse of the jobs change and the real-pay change, each relative to the typical occupation.
    gfc_jobs, gfc_jpar, gfc_base = native_relative(jobsall00[2009], jobsall00[2008], jobsall00[2008], gjobsall00[2009], gjobsall00[2008])
    cv00 = piv(FT, 2000, "median_cv")
    gpay00 = piv(GFT, 2000, "median")
    gfc_pay, gfc_ppar, gfc_pay_base = pay_relative(pay00[2009] / cpi[2009], pay00[2008] / cpi[2008], cv00[2009], cv00[2008],
                                                   gpay00[2009] / cpi[2009], gpay00[2008] / cpi[2008])
    gfc_both = pd.concat({"jobs": gfc_jobs, "pay": gfc_pay, "jpar": gfc_jpar, "ppar": gfc_ppar}, axis=1)
    gfc_both["headline"] = gfc_both[["jobs", "pay"]].min(axis=1)
    gfc_both["from_pay"] = (gfc_both["pay"] < gfc_both["jobs"]).astype(float).where(gfc_both[["jobs", "pay"]].notna().all(axis=1),
                                                                                   gfc_both["jobs"].isna().astype(float))
    gfc_both["par"] = np.where(gfc_both["from_pay"] > 0.5, gfc_both["ppar"], gfc_both["jpar"])
    gfc10 = to10(gfc_both["headline"].dropna())
    gfc20 = to20(gfc10["value"])
    gfc_par20 = to20(to10(gfc_both["par"].dropna())["value"])
    gfc_jobs20 = to20(to10(gfc_both["jobs"].dropna())["value"])["value"]
    gfc_pay20 = to20(to10(gfc_both["pay"].dropna())["value"])["value"]
    gfc_frompay20 = to20(to10(gfc_both["from_pay"].dropna())["value"])["value"]
    dom0_20 = to20(gfc10["dominant"])["value"]
    col4 = rel_change(pay20[2023] / cpi[2023], pay20[2021] / cpi[2021])
    col_base = float(col4.dropna().median())
    colg = rel_change(gpay20[2023] / cpi[2023], gpay20[2021] / cpi[2021])

    adv = pd.read_excel(raw / "ons_online_adverts" / "onlinejobadvertestimatesdataset241024.xlsx", sheet_name="Adverts by category Feb 2020", header=6)
    adv = adv.dropna(subset=["Date"]).set_index("Date")
    cats = [c for c in adv.columns if c not in ("Notes",)]
    adv = adv[cats].apply(pd.to_numeric, errors="coerce")
    peak, slump = adv.loc["2022-01-01":"2022-06-30"].mean(), adv.loc["2024-01-01":"2024-10-31"].mean()
    trough = adv.loc["2020-04-01":"2020-06-30"].mean()
    tech = np.log(slump / peak)
    tech_rel = tech - tech["All industries"]
    covid_adv = np.log(trough / 100.0)
    covid_adv_rel = covid_adv - covid_adv["All industries"]

    # ---------------- Young workers (APS 2016, includes self-employed) ----------------
    aps = pd.read_excel(raw / "ons_age_bands" / "4digitoccupationand4digitindustrybyagebandsfinal.xls", sheet_name="OCCUPATION", header=None)
    region_row = aps.iloc[6].astype(str).str.strip()
    # The UK block is labelled "Total" on the OCCUPATION sheet (Great Britain is a separate sheet).
    starts = [c for c in range(aps.shape[1]) if region_row[c] in ("United Kingdom", "UK", "Total")]
    if not starts:
        raise SystemExit(f"APS: no UK block; regions found: {sorted(set(region_row) - {'nan'})}")
    s0 = starts[0]
    ages = aps.iloc[7].astype(str).str.strip()
    total_cols = [c for c in range(s0, min(s0 + 21, aps.shape[1])) if ages[c].lower().startswith(("total", "all"))]
    young_col, total_col = s0 + 2, (total_cols[0] + 2 if total_cols else s0 + 20)
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
    young10 = share4.copy()
    young_par = pd.Series(0.0, index=share4.index)
    for code in share4.index:
        if pd.isna(share4[code]) and code[:3] in parent_share.index:
            young10[code], young_par[code] = parent_share[code[:3]], 1.0
    young20, young_par20 = to20(young10.dropna()), to20(young_par)

    # ---------------- Occupations ----------------
    dominant10 = comp.groupby("soc2020").weight.max()
    occupations = []
    for soc in socs:
        r = now.loc[soc]
        m = {}
        conf, cvflags = cv_conf(r["median_cv"])
        base_flags = ["employees_only", "provisional"] + cvflags
        if pd.notna(r["median"]):
            m["pay_median"] = metric(r["median"], "GBP/year", 2025, "ons_ashe_t14", "Median gross annual pay, full-time employees; range is the 25th to 75th percentile.",
                                     low=r["p25"], high=r["p75"], confidence=conf, flags=base_flags, nd=0)
        elif soc[:3] in gnow.index and pd.notna(gnow.loc[soc[:3], "median"]):
            g = gnow.loc[soc[:3]]
            m["pay_median"] = metric(g["median"], "GBP/year", 2025, "ons_ashe_t14", f"Median full-time pay for the wider group '{g['title']}' (this occupation's own figure is suppressed).",
                                     low=g["p25"], high=g["p75"], granularity="parent_group", confidence="low", flags=["employees_only", "provisional", "imputed_parent"], nd=0)
        else:
            m["pay_median"] = metric(None, "GBP/year", 2025, "ons_ashe_t14", "Median pay is suppressed for this occupation and its group.", confidence="low", flags=["suppressed", "employees_only"])
        for key, col, label in (("pay_p10", "p10", "10th percentile (floor)"), ("pay_p90", "p90", "90th percentile (a ceiling)")):
            v = r[col]
            m[key] = metric(v, "GBP/year", 2025, "ons_ashe_t14", f"{label} of gross annual pay, full-time employees.",
                            confidence=conf if pd.notna(v) else "low", flags=base_flags + ([] if pd.notna(v) else ["suppressed"]), nd=0)
        rp15, rp25 = real_pay[2015].get(soc, np.nan), real_pay[2025].get(soc, np.nan)
        dom = float(dominant10.get(soc, 0))
        m["real_pay_change_10y"] = metric(rp25 / rp15 - 1 if pd.notna(rp15) and pd.notna(rp25) else None, "fraction", "2015-2025", "ons_ashe_t14",
                                          "Real change in median full-time pay, 2015 to 2025, in April 2025 prices (CPIH).",
                                          confidence="medium" if dom >= 0.8 else "low",
                                          flags=["bridged_soc2010", "employees_only", "provisional"] + ([] if pd.notna(rp15) and pd.notna(rp25) else ["suppressed"]))
        m["jobs"] = metric(r["jobs_k"], "thousand jobs", 2025, "ons_ashe_t14", "Full-time employee jobs (ASHE estimate, rounded to the thousand).",
                           confidence="medium" if pd.notna(r["jobs_k"]) else "low", flags=base_flags + ([] if pd.notna(r["jobs_k"]) else ["suppressed"]), nd=1)
        years = range(2021, 2026)
        trend, gran, tflags, note = None, "occupation", ["employees_only", "provisional"], "full-time employee jobs"
        for source, g, f, n in ((jobs20, "occupation", [], "full-time employee jobs"),
                                (jobsall20, "occupation", [], "all employee jobs (full- and part-time)"),
                                (gjobs20, "parent_group", ["imputed_parent"], "full-time jobs in the wider occupation group")):
            key = soc if g == "occupation" else soc[:3]
            if key in source.index:
                trend = theil(years, [source.loc[key].get(y, np.nan) for y in years])
                if trend:
                    gran, tflags, note = g, ["employees_only", "provisional"] + f, n
                    break
        m["demand_trend"] = metric(trend[0] if trend else None, "fraction/year", "2021-2025", "ons_ashe_t14",
                                   f"Robust (Theil-Sen) yearly trend in {note} since the 2021 code change; range is a 90% interval.",
                                   low=trend[1] if trend else None, high=trend[2] if trend else None, granularity=gran,
                                   confidence=("low" if gran == "parent_group" else trend_conf(trend[2] - trend[1])) if trend else "low",
                                   flags=tflags + ([] if trend else ["suppressed"]))
        t0, note0 = None, "full-time employee jobs"
        for series_by_year, n in ((jobs_by_year, "full-time employee jobs"), (jobsall_by_year, "all employee jobs")):
            t0 = theil(range(2011, 2020), [series_by_year[y].get(soc, np.nan) for y in range(2011, 2020)])
            if t0:
                note0 = n
                break
        m["demand_trend_2011_19"] = metric(t0[0] if t0 else None, "fraction/year", "2011-2019", "ons_ashe_t14",
                                           f"Robust yearly trend in {note0} in the previous code era, bridged to today's code; range is a 90% interval.",
                                           low=t0[1] if t0 else None, high=t0[2] if t0 else None,
                                           confidence=(trend_conf(t0[2] - t0[1]) if dom >= 0.8 else "low") if t0 else "low",
                                           flags=["bridged_soc2010", "employees_only", "provisional"] + ([] if t0 else ["suppressed"]))
        e = expo.get(soc)
        if e:
            low, high = max(0.0, e["mean"] - e["sd"]), min(1.0, e["mean"] + e["sd"])
            flags = (["multi_isco"] if e["n_isco"] > 1 else []) + (["imputed_parent"] if e["imputed"] else [])
            dp, ip = dfe_pct.get(soc, np.nan), ilo_pct.get(soc, np.nan)
            extra = {"gradient": e["gradient"], "dominant_isco": e["dominant_isco"], "n_isco": e["n_isco"],
                     "ilo_percentile": num(ip, 3), "dfe_percentile": num(dp, 3)}
            if pd.notna(dp) and pd.notna(ip) and abs(ip - dp) > 0.30:
                on_ilo = float(np.quantile(ilo_vals.values, dp))
                low, high = min(low, on_ilo), max(high, on_ilo)
                flags.append("sources_disagree")
            m["exposure"] = metric(e["mean"], "score 0-1", 2025, "ilo_wp140",
                                   "Generative-AI exposure of the occupation's tasks (ILO), averaged over the international codes its job titles map to; range shows their spread and any disagreement with the UK (DfE) estimate.",
                                   low=low, high=high, granularity="parent_group" if e["imputed"] else "occupation",
                                   confidence="low" if (e["imputed"] or "sources_disagree" in flags) else ("high" if e["sd"] <= 0.05 else "medium" if e["sd"] <= 0.10 else "low"),
                                   flags=flags, extra=extra)
        else:
            m["exposure"] = metric(None, "score 0-1", 2025, "ilo_wp140", "No exposure estimate for this occupation or its group.", confidence="low", flags=["suppressed"])
        dpv = dfe_pct.get(soc, np.nan)
        m["exposure_uk"] = metric(dpv, "score 0-1", 2023, "dfe_ai_uk_2023",
                                  "Percentile rank of the DfE's LLM exposure score among UK occupations (1 = most exposed); a cross-check, not a second headline number.",
                                  confidence="medium" if pd.notna(dpv) else "low", flags=["bridged_soc2010"] + ([] if pd.notna(dpv) else ["suppressed"]))
        cv_ = covid20["value"].get(soc, np.nan)
        par = covid_par20["value"].get(soc, 0.0) if soc in covid_par20.index else 0.0
        cat = category_of(soc)
        m["resilience_covid"] = metric(math.expm1(cv_) if pd.notna(cv_) else None, "fraction", "2019-2020", "ons_ashe_t14",
                                       "Change in all-employee jobs from 2019 to 2020 compared with the typical occupation (+0.10 = 10 points better).",
                                       granularity="parent_group" if par > 0.5 else "occupation",
                                       confidence="low" if (pd.isna(cv_) or par > 0.5 or abs(cv_) > 0.4 or dom < 0.8) else "medium",
                                       flags=["covid_year", "bridged_soc2010", "employees_only"] + (["imputed_parent"] if par > 0.5 else []) + ([] if pd.notna(cv_) else ["suppressed"]),
                                       extra={"adverts_category": cat, "adverts_vs_all_2020": num(math.expm1(covid_adv_rel.get(cat, np.nan)))})
        c4 = col4.get(soc, np.nan)
        if pd.notna(c4):
            cval, cgran, cflags = c4 - col_base, "occupation", ["employees_only"]
        elif pd.notna(colg.get(soc[:3], np.nan)):
            cval, cgran, cflags = colg[soc[:3]] - col_base, "parent_group", ["employees_only", "imputed_parent"]
        else:
            cval, cgran, cflags = np.nan, "occupation", ["employees_only", "suppressed"]
        m["resilience_cost_of_living"] = metric(math.expm1(cval) if pd.notna(cval) else None, "fraction", "2021-2023", "ons_ashe_t14",
                                                "Real pay change from 2021 to 2023 compared with the typical occupation (+0.05 = 5 points better).",
                                                granularity=cgran, confidence="medium" if cgran == "occupation" and pd.notna(cval) else "low", flags=cflags)
        tv = tech_rel.get(cat, np.nan)
        m["resilience_tech_slump"] = metric(math.expm1(tv) if pd.notna(tv) else None, "fraction", "2022-2024", "ons_online_job_adverts",
                                            f"Change in online job adverts for the '{cat}' category from the first half of 2022 to 2024, compared with all adverts.",
                                            granularity="estimate", confidence="medium" if pd.notna(tv) else "low",
                                            flags=["category_level"] + ([] if pd.notna(tv) else ["suppressed"]), extra={"adverts_category": cat})
        gv = gfc20["value"].get(soc, np.nan)
        gpar = gfc_par20["value"].get(soc, 0.0) if soc in gfc_par20.index else 0.0
        chain_ok = dom >= 0.8 and dom0_20.get(soc, 0.0) >= 0.8
        gj, gp, gfp = gfc_jobs20.get(soc, np.nan), gfc_pay20.get(soc, np.nan), gfc_frompay20.get(soc, np.nan)
        m["resilience_2008"] = metric(math.expm1(gv) if pd.notna(gv) else None, "fraction", "2008-2009", "ons_ashe_t14",
                                      "The worse of two hits from April 2008 to April 2009, each compared with the typical occupation: change in all-employee jobs and change in real full-time pay. Measured in the old SOC 2000 codes and carried to today's code.",
                                      granularity="parent_group" if gpar > 0.5 else "occupation",
                                      confidence="medium" if (pd.notna(gv) and chain_ok and gpar <= 0.5 and abs(gv) <= 0.4) else "low",
                                      flags=["bridged_soc2000", "bridged_soc2010", "employees_only"] + (["imputed_parent"] if gpar > 0.5 else []) + ([] if pd.notna(gv) else ["suppressed"]),
                                      extra={"jobs_vs_typical": num(math.expm1(gj)) if pd.notna(gj) else None,
                                             "real_pay_vs_typical": num(math.expm1(gp)) if pd.notna(gp) else None,
                                             "headline_from": None if pd.isna(gfp) else ("real_pay" if gfp > 0.5 else "jobs")})
        yv = young20["value"].get(soc, np.nan)
        ypar = young_par20["value"].get(soc, 0.0) if soc in young_par20.index else 0.0
        m["young_worker_share"] = metric(yv, "fraction", 2016, "ons_aps_2016_age",
                                         "Share of people in this job aged 16 to 24 in 2016, including self-employed: a sign of how open it is to young entrants.",
                                         granularity="parent_group" if ypar > 0.5 else "occupation",
                                         confidence="medium" if (pd.notna(yv) and ypar <= 0.5 and dom >= 0.8) else "low",
                                         flags=["bridged_soc2010"] + (["imputed_parent"] if ypar > 0.5 else []) + ([] if pd.notna(yv) else ["suppressed"]))
        occupations.append({"soc2020": soc, "title": titles.get(soc, soc), "short_title": DEMO.get(soc, titles.get(soc, soc)),
                            "isco08": [{"code": c, "share": round(float(s), 4)} for c, s in
                                       isco[isco.soc2020 == soc].sort_values("share", ascending=False)[["isco08", "share"]].itertuples(index=False)],
                            "in_demo_set": soc in DEMO, "metrics": m})

    # ---------------- Hedges ----------------
    cand = json.loads((proc / "hedges_candidates.json").read_text(encoding="utf-8"))
    hedges = {}
    for soc in socs:
        entry = cand.get(soc, {"candidates": []})
        hedges[soc] = [{"soc2020": c["soc2020"], "title": titles.get(c["soc2020"], c["soc2020"]), "similarity": c["similarity"],
                        "shared_skills": c["shared_skills"], "evidence": c["evidence"], "status": "preliminary",
                        "why": f"Shares {c['n_shared']} skills, e.g. {', '.join(c['shared_skills'][:3])}" + ("; estimate from few job-title links" if c["evidence"] == "estimate" else "")}
                       for c in entry["candidates"]]

    # ---------------- Backtest ----------------
    windows, spear = [], {}
    for base in (2013, 2014):
        end = base + 5
        d = pd.DataFrame({"pay": pay10[base], "prior": rel_change(jobs10[base], jobs10[2011]),
                          "rpg": rel_change(pay10[end] / cpi[end], pay10[base] / cpi[base]), "jg": rel_change(jobs10[end], jobs10[base])}).dropna()
        amb, safe = d.pay >= d.pay.quantile(2 / 3), d.prior >= d.prior.quantile(2 / 3)
        spear[str(base)] = {"pay_level_vs_later_real_pay_growth": round(float(d[["pay", "rpg"]].corr("spearman").iloc[0, 1]), 3),
                            "prior_jobs_growth_vs_later_jobs_growth": round(float(d[["prior", "jg"]].corr("spearman").iloc[0, 1]), 3)}

        def group(key, label, mask):
            rp, jg = boot(d[mask].rpg), boot(d[mask].jg)
            return {"key": key, "label": label, "n": int(mask.sum()),
                    "real_pay_growth": {"median": num(math.expm1(rp[0])), "low": num(math.expm1(rp[1])), "high": num(math.expm1(rp[2]))},
                    "jobs_growth": {"median": num(math.expm1(jg[0])), "low": num(math.expm1(jg[1])), "high": num(math.expm1(jg[2]))},
                    "share_jobs_fell": num(float((d[mask].jg < 0).mean()))}
        dom_src = comp.sort_values("weight", ascending=False).drop_duplicates("soc2020").set_index("soc2020")["soc2010"]
        occ_rows = []
        for soc in socs:
            src = dom_src.get(soc)
            if src in d.index:
                occ_rows.append({"soc2020": soc, "group_then": "ambitious" if amb[src] else "safe" if safe[src] else "other",
                                 "real_pay_growth": num(math.expm1(d.loc[src, "rpg"])), "jobs_growth": num(math.expm1(d.loc[src, "jg"])), "flags": ["bridged_soc2010"]})
        windows.append({"base_year": base, "outcome_year": end, "horizon": 5, "coding": "SOC 2010 native", "flags": [], "jobs_comparable": True,
                        "groups": [group("ambitious", "Ambitious then: top third by pay", amb), group("safe", "Safe then: top third by prior jobs growth (2011 on)", safe),
                                   None, group("all", "All occupations with complete data", d.pay.notna())], "occupations": occ_rows})
    sp = pd.DataFrame({y: real_pay[y] for y in real_pay})
    sj = pd.DataFrame({y: jobs_by_year[y] for y in range(2011, 2021)})
    d = pd.DataFrame({"pay": sp[2019], "prior": rel_change(sj[2019], sj[2015]), "rpg": rel_change(sp[2024], sp[2019])}).dropna()
    amb, safe = d.pay >= d.pay.quantile(2 / 3), d.prior >= d.prior.quantile(2 / 3)

    def pay_group(key, label, mask):
        rp = boot(d[mask].rpg)
        return {"key": key, "label": label, "n": int(mask.sum()), "real_pay_growth": {"median": num(math.expm1(rp[0])), "low": num(math.expm1(rp[1])), "high": num(math.expm1(rp[2]))},
                "jobs_growth": None, "share_jobs_fell": None}
    windows.append({"base_year": 2019, "outcome_year": 2024, "horizon": 5, "coding": "bridged SOC 2010 -> SOC 2020", "flags": ["bridged_soc2010", "covid_year", "recoded_2021"],
                    "jobs_comparable": False, "groups": [pay_group("ambitious", "Ambitious then: top third by pay", amb),
                                                          pay_group("safe", "Safe then: top third by prior jobs growth (2015-19)", safe), None,
                                                          pay_group("all", "All occupations with complete data", d.pay.notna())],
                    "occupations": [{"soc2020": s, "group_then": "ambitious" if amb[s] else "safe" if safe[s] else "other", "real_pay_growth": num(math.expm1(d.loc[s, "rpg"])),
                                     "jobs_growth": None, "flags": ["bridged_soc2010", "covid_year"]} for s in socs if s in d.index]})

    # ---------------- Evaluation ----------------
    def seam(bridged_pay, native_pay, bridged_jobs, native_jobs):
        out = {}
        for name, b, n in (("pay", bridged_pay, native_pay), ("jobs", bridged_jobs, native_jobs)):
            r = (n / b).replace([np.inf, -np.inf], np.nan).dropna()
            out[name] = {"n": int(len(r)), "median_ratio": num(r.median(), 3), "iqr": [num(r.quantile(.25), 3), num(r.quantile(.75), 3)],
                         "share_outside_0.8_1.25": num(float(((r < 0.8) | (r > 1.25)).mean()), 3)}
        return out
    split0 = pd.read_csv(proc / "soc2000_to_soc2010.csv", dtype={"soc2000": str, "soc2010": str})
    j0 = split0.merge(jobsall00[2010].rename("v").rename_axis("soc2000").reset_index(), on="soc2000").dropna(subset=["v"])
    hv = pd.read_csv(proc / "hedge_validation.csv", dtype={"soc2020": str})
    demo_dis = [{"soc2020": s, "ilo_percentile": num(ilo_pct.get(s), 3), "dfe_percentile": num(dfe_pct.get(s), 3)}
                for s in DEMO if pd.notna(dfe_pct.get(s)) and pd.notna(ilo_pct.get(s)) and abs(ilo_pct[s] - dfe_pct[s]) > 0.30]
    checks = {
        "bridge_seam": {"status": "preliminary", "date": NOW[:10], "summary": "Bridged vs native values at both code changes: pay lines up, job counts do not.",
                        "metrics": {"2020_2021": seam(pay_by_year[2020], pay20[2021], jobs_by_year[2020], jobs20[2021]),
                                    "2010_2011_all_employees": seam(to10(piv(ALL, 2000, "median")[2010])["value"], piv(ALL, 2010, "median")[2011],
                                                                    (j0.share * j0.v).groupby(j0.soc2010).sum(), jobsall10[2011])}},
        "backtest_probe": {"status": "preliminary", "date": NOW[:10], "summary": "Spearman correlations in the two native windows.", "metrics": spear},
        "exposure_agreement": {"status": "preliminary", "date": NOW[:10], "summary": "ILO (weighted) vs DfE LLM exposure, rank correlation across occupations.",
                               "metrics": {"spearman": round(rho, 3), "n": int(len(both)), "demo_disagreements_over_30_points": demo_dis}},
        "hedge_sanity": {"status": "preliminary", "date": NOW[:10], "summary": "Share of top-3 hedges that O*NET (US) also lists as related, vs two baselines.",
                         "metrics": {"n": int(len(hv)), "hit_at_3": num(hv.hit_at_3.mean(), 3), "baseline_random_same_level": num(hv.random_same_level.mean(), 3),
                                     "baseline_same_3_digit_group": num(hv.same_minor_group.dropna().mean(), 3),
                                     "demo_hit_at_3": num(hv[hv.soc2020.isin(list(DEMO))].hit_at_3.mean(), 3),
                                     "demo_zero_hits": hv[hv.soc2020.isin(list(DEMO)) & (hv.hit_at_3 == 0)].soc2020.tolist()}},
        "matcher": {"status": "pending", "date": None, "summary": "Keyword vs off-the-shelf embeddings vs fine-tuned, on held-out human labels (labels not collected yet).", "metrics": {}},
    }

    crises = [
        {"key": "covid", "label": "COVID-19", "window": "2019-2020", "measure": "All-employee jobs, relative to the median occupation",
         "baseline_median": num(math.expm1(covid_base)), "status": "preliminary", "flags": ["covid_year", "bridged_soc2010"]},
        {"key": "cost_of_living", "label": "Cost-of-living shock", "window": "2021-2023", "measure": "Real median full-time pay, relative to the median occupation",
         "baseline_median": num(math.expm1(col_base)), "status": "preliminary", "flags": []},
        {"key": "tech_slump", "label": "Tech hiring slump", "window": "2022-2024", "measure": "Online job adverts by category, relative to all adverts",
         "baseline_median": num(math.expm1(tech["All industries"])), "status": "preliminary", "flags": ["category_level"]},
        {"key": "gfc_2008", "label": "2008 financial crisis", "window": "2008-2009",
         "measure": "Worse of all-employee jobs change and real full-time pay change (SOC 2000), each relative to the median occupation",
         "baseline_median": num(math.expm1(gfc_base)), "baseline_real_pay_median": num(math.expm1(gfc_pay_base)),
         "status": "preliminary", "flags": ["bridged_soc2000", "bridged_soc2010"]},
    ]

    meta = {"schema_version": SCHEMA_VERSION, "generated_at": NOW}
    fit = {**meta, "status": "mock", "method": "hand-assigned placeholder affinities until the matcher is evaluated",
           "tags": [{"id": t, "label": lbl, "keywords": kws} for t, lbl, kws in TAGS], "affinity": AFFINITY}
    method = ("Pre-registered naive tiers, nothing tuned to outcomes. Ambitious: top third by pay at the base year. Safe: top third by prior jobs growth. "
              "Outcomes 5 years later; real pay in CPIH-deflated terms.")
    caveats = ["Historical tiers use market data only: no historical AI exposure index exists.", "Windows overlap, so they are not independent.",
               "Only occupations with complete data are included (larger occupations).",
               "Low-pay occupations gained from minimum-wage rises after 2016, which lowers the Ambitious group's relative pay growth.",
               "Windows crossing 2021 compare pay only; job counts are not comparable across the code change.", "The 2019-2024 window includes the 2020 COVID year."]
    for out_dir, subset in ((snap, None), (snap / "mock", set(DEMO))):
        keep = (lambda s: True) if subset is None else (lambda s: s in subset)
        write(out_dir, "occupations", {**meta, "status": "preliminary", "price_base": "CPIH, April 2025 prices", "demo_set": list(DEMO),
                                       "occupations": [o for o in occupations if keep(o["soc2020"])]})
        write(out_dir, "history", {**meta, "status": "preliminary", "occupations": {k: v for k, v in history.items() if keep(k)}})
        write(out_dir, "hedges", {**meta, "status": "preliminary", "method": "ESCO skill overlap (IDF-weighted Jaccard), same ONS skill level; checked against O*NET",
                                  "occupations": {k: v for k, v in hedges.items() if keep(k)}})
        write(out_dir, "fit", fit)
        write(out_dir, "backtest", {**meta, "status": "preliminary", "method": method, "caveats": caveats,
                                    "windows": [{**w, "occupations": [o for o in w["occupations"] if keep(o["soc2020"])]} for w in windows]})
        write(out_dir, "crises", {**meta, "status": "preliminary", "crises": crises})
        write(out_dir, "sources", {**meta, "status": "preliminary", "sources": SOURCES})
        write(out_dir, "eval", {**meta, "status": "preliminary", "checks": checks})
    print(f"occupations: {len(occupations)}; demo: {sum(o['in_demo_set'] for o in occupations)}; hedges for {sum(bool(v) for v in hedges.values())}; "
          f"windows: {len(windows)}; exposure spearman {rho:.2f} (n={len(both)})")


if __name__ == "__main__":
    main()
