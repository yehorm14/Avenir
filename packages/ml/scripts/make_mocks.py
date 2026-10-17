"""Generate snapshots/ml/mock/*.json in the final contract shapes.

Usage: python -I make_mocks.py RAW_DIR PROCESSED_DIR OUT_DIR

Values are real where the pipeline already computes them (status "preliminary"):
pay level and range, jobs, real pay path, demand trends, ILO exposure (weighted
over mapped ISCO codes), COVID and cost-of-living resilience, backtest windows,
crisis baselines, bridge seam check. Hedges and fit affinities are placeholders
(status "mock"). DfE exposure, tech slump and 2008 are "pending" (value null).
Only the 20-occupation demo set is written, to keep fixtures small.
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

RNG = np.random.default_rng(0)
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

DEMO = {
    "2134": "Software developer", "3544": "Data analyst", "2133": "IT business analyst or systems designer",
    "2135": "Cyber security professional", "2141": "Web designer", "2142": "Graphic and multimedia designer",
    "2451": "Architect", "2452": "Architectural technologist or planner", "3120": "CAD and architectural technician",
    "2121": "Civil engineer", "2123": "Electrical engineer", "3113": "Engineering technician",
    "2453": "Quantity surveyor", "2454": "Chartered surveyor", "2433": "Actuary, economist or statistician",
    "2422": "Finance and investment analyst", "2421": "Accountant", "2254": "Medical radiographer",
    "5241": "Electrician", "2313": "Secondary school teacher",
}

TAGS = [
    ("maths", "Maths and numbers", ["math", "maths", "numbers", "algebra", "calculus", "equation", "statistic"]),
    ("art_drawing", "Art and drawing", ["draw", "art", "paint", "sketch", "illustrat"]),
    ("design", "Design and visuals", ["design", "layout", "typograph", "visual", "graphics", "ux"]),
    ("computers_coding", "Computers and coding", ["code", "coding", "program", "software", "computer", "app", "python"]),
    ("data", "Data and spreadsheets", ["data", "spreadsheet", "excel", "analys", "chart", "trend"]),
    ("building_spaces", "Buildings and spaces", ["building", "architect", "house", "interior", "cities", "construction"]),
    ("engineering_making", "Engineering and making things", ["engineer", "make things", "build things", "lego", "robot", "machine"]),
    ("fixing_hands_on", "Fixing things, hands-on", ["fix", "repair", "hands-on", "tools", "wiring", "bike", "practical"]),
    ("electricity_energy", "Electricity and energy", ["electric", "electronic", "circuit", "energy", "solar", "power"]),
    ("science_health", "Science and health", ["biology", "medicine", "medical", "health", "hospital", "physics", "science"]),
    ("helping_people", "Helping people", ["help people", "caring", "patient", "community", "support people"]),
    ("teaching_explaining", "Teaching and explaining", ["teach", "explain", "tutor", "coach", "mentor"]),
    ("money_business", "Money and business", ["money", "financ", "invest", "business", "stock", "economic", "trading"]),
    ("security_puzzles", "Security and puzzles", ["security", "hacking", "cyber", "puzzle", "cipher"]),
    ("writing_language", "Writing and languages", ["writ", "language", "english", "stories", "translat"]),
    ("outdoors_maps", "Outdoors and maps", ["outdoor", "map", "geograph", "landscape", "survey"]),
]

# Placeholder affinities (status "mock") until the matcher (M1) produces real ones.
AFFINITY = {
    "maths": {"2433": 0.95, "2422": 0.8, "2421": 0.75, "3544": 0.8, "2134": 0.6, "2121": 0.6, "2123": 0.6, "2453": 0.6, "2313": 0.5, "2135": 0.4},
    "art_drawing": {"2142": 0.95, "2141": 0.7, "2451": 0.75, "3120": 0.6, "2452": 0.4},
    "design": {"2142": 0.9, "2141": 0.9, "2451": 0.8, "3120": 0.6, "2452": 0.5, "2133": 0.3},
    "computers_coding": {"2134": 0.95, "2135": 0.8, "2141": 0.7, "2133": 0.7, "3544": 0.6, "3120": 0.4},
    "data": {"3544": 0.95, "2433": 0.85, "2422": 0.7, "2133": 0.6, "2421": 0.6, "2134": 0.4},
    "building_spaces": {"2451": 0.95, "2452": 0.85, "3120": 0.8, "2121": 0.75, "2453": 0.7, "2454": 0.7},
    "engineering_making": {"2121": 0.9, "2123": 0.9, "3113": 0.9, "5241": 0.6, "2134": 0.3},
    "fixing_hands_on": {"5241": 0.95, "3113": 0.85, "2123": 0.5, "2254": 0.3},
    "electricity_energy": {"2123": 0.95, "5241": 0.9, "3113": 0.6},
    "science_health": {"2254": 0.95, "2313": 0.3, "2433": 0.3},
    "helping_people": {"2254": 0.8, "2313": 0.85},
    "teaching_explaining": {"2313": 0.95, "2433": 0.3},
    "money_business": {"2422": 0.95, "2421": 0.9, "2433": 0.7, "2453": 0.5, "2454": 0.5},
    "security_puzzles": {"2135": 0.95, "2134": 0.5, "2433": 0.3},
    "writing_language": {"2313": 0.4, "2133": 0.3},
    "outdoors_maps": {"2454": 0.8, "2121": 0.6, "2453": 0.4, "2452": 0.5},
}

SOURCES = {
    "ons_ashe_t14": {"name": "Annual Survey of Hours and Earnings, Table 14 (occupation by 4-digit SOC)", "publisher": "ONS",
                     "url": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14",
                     "licence": "Open Government Licence v3.0", "coverage": "UK employees; excludes self-employed", "years": "2011-2025",
                     "status": "loaded", "notes": "SOC 2010 until 2020, SOC 2020 from 2021; 2018 and 2025 provisional"},
    "ons_cpih": {"name": "CPIH index (L522)", "publisher": "ONS", "url": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23",
                 "licence": "Open Government Licence v3.0", "coverage": "UK", "years": "1988-2026", "status": "loaded", "notes": "April values used, the ASHE reference month"},
    "ons_soc_crosswalk": {"name": "Relationship between SOC 2010 and SOC 2020 (July 2021 tables)", "publisher": "ONS",
                          "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/therelationshipbetweenstandardoccupationalclassification2010andstandardoccupationalclassification2020",
                          "licence": "Open Government Licence v3.0", "coverage": "UK (LFS 2014-16, Census 2011 E&W)", "years": "2021", "status": "loaded", "notes": "Used to bridge pre-2021 data"},
    "ons_soc_coding_index": {"name": "SOC 2020 Volume 2: the coding index", "publisher": "ONS",
                             "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions",
                             "licence": "Open Government Licence v3.0", "coverage": "UK job titles", "years": "2026", "status": "loaded", "notes": "Job title to SOC 2020 and ISCO-08"},
    "ilo_wp140": {"name": "Generative AI and Jobs: A Refined Global Index of Occupational Exposure (Working Paper 140)", "publisher": "ILO",
                  "url": "https://webapps.ilo.org/static/english/intserv/working-papers/wp140/index.html",
                  "licence": "To confirm before public release", "coverage": "427 ISCO-08 occupations", "years": "2025", "status": "loaded", "notes": "Mean task exposure and its spread per occupation"},
    "dfe_ai_uk_2023": {"name": "The impact of AI on UK jobs and training", "publisher": "Department for Education",
                       "url": "https://www.gov.uk/government/publications/the-impact-of-ai-on-uk-jobs-and-training",
                       "licence": "Open Government Licence v3.0", "coverage": "UK SOC 2020", "years": "2023", "status": "pending", "notes": "UK cross-check for exposure"},
    "ons_online_job_adverts": {"name": "Online job advert estimates", "publisher": "ONS", "url": "https://www.ons.gov.uk/",
                               "licence": "Open Government Licence v3.0", "coverage": "UK", "years": "2018-", "status": "pending", "notes": "Tech slump 2022-24"},
    "census_occupation": {"name": "Census 2011 and 2021 occupation (England and Wales); Scotland 2011 and 2022", "publisher": "ONS / NRS",
                          "url": "https://www.nomisweb.co.uk/", "licence": "Open Government Licence v3.0", "coverage": "Includes self-employed",
                          "years": "2011, 2021/2022", "status": "pending", "notes": "Self-employed coverage"},
    "esco": {"name": "ESCO v1.2.1 classification", "publisher": "European Commission", "url": "https://esco.ec.europa.eu/",
             "licence": "EU open data (attribution)", "coverage": "About 3,000 occupations and 14,000 skills", "years": "2025",
             "status": "pending", "notes": "Skills for hedges and matcher training text"},
}


def num(x, nd=4):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return round(x, nd)


def metric(value, unit, as_of, source, note, low=None, high=None, granularity="occupation", confidence="medium",
           flags=(), status="preliminary", extra=None, nd=4):
    return {"value": num(value, nd), "low": num(low, nd), "high": num(high, nd), "unit": unit, "as_of": str(as_of),
            "source": source, "granularity": granularity, "confidence": confidence, "flags": sorted(set(flags)),
            "status": status, "note": note, "extra": extra or {}}


def cv_conf(cv):
    if cv is None or (isinstance(cv, float) and math.isnan(cv)):
        return "low", []
    if cv <= 5:
        return "high", []
    if cv <= 10:
        return "medium", []
    return "low", ["cv_high"]


def cpih_april(path: Path) -> dict:
    df = pd.read_csv(path, header=None, names=["period", "value"])
    df = df[df["period"].astype(str).str.fullmatch(r"\d{4} APR")]
    return {int(p[:4]): float(v) for p, v in zip(df["period"], df["value"])}


def bridged_series(ft: pd.DataFrame, comp: pd.DataFrame, split: pd.DataFrame, cpi: dict) -> pd.DataFrame:
    old = ft[ft.soc_version == 2010][["year", "soc_code", "median", "jobs_k"]].rename(columns={"soc_code": "soc2010"})
    new = ft[ft.soc_version == 2020][["year", "soc_code", "median", "jobs_k"]].rename(columns={"soc_code": "soc2020"})
    pay = comp.merge(old, on="soc2010").dropna(subset=["median"])
    pay = pay[pay.weight > 0].assign(wx=lambda d: d.weight * d["median"])
    s = pay.groupby(["soc2020", "year"])[["wx", "weight"]].sum()
    bp = (s.wx / s.weight).rename("median")
    jobs = split.merge(old, on="soc2010").dropna(subset=["jobs_k"]).assign(part=lambda d: d.share * d.jobs_k)
    bj = jobs.groupby(["soc2020", "year"])["part"].sum().rename("jobs_k")
    bridged = pd.concat([bp, bj], axis=1).reset_index().assign(bridged=True)
    out = pd.concat([bridged, new.assign(bridged=False)], ignore_index=True)
    out["real"] = out["median"] * cpi[2025] / out["year"].map(cpi)
    return out


def theil(years, values):
    years, values = np.asarray(years, float), np.asarray(values, float)
    ok = np.isfinite(values) & (values > 0)
    if ok.sum() < 4:
        return None
    slope, _, lo, hi = theilslopes(np.log(values[ok]), years[ok], alpha=0.90)
    return math.expm1(slope), math.expm1(lo), math.expm1(hi)


def trend_conf(width):
    return "high" if width <= 0.08 else "medium" if width <= 0.20 else "low"


def boot(values, n=2000):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if len(values) < 5:
        return None, None, None
    draws = np.median(RNG.choice(values, size=(n, len(values)), replace=True), axis=1)
    return float(np.median(values)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def write(out_dir: Path, name: str, payload: dict) -> None:
    (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    raw, proc, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    cpi = cpih_april(raw / "ons_cpih" / "cpih_index_l522.csv")
    a = pd.read_parquet(proc / "ashe_long.parquet")
    ft, allemp = a[a.sheet == "Full-Time"], a[a.sheet == "All"]
    comp = pd.read_csv(proc / "soc2020_from_soc2010.csv", dtype={"soc2020": str, "soc2010": str})
    split = pd.read_csv(proc / "soc2010_to_soc2020.csv", dtype={"soc2010": str, "soc2020": str})
    ilo = pd.read_csv(proc / "ilo_exposure.csv", dtype={"isco08": str})
    series = bridged_series(ft, comp, split, cpi)
    dominant = comp.sort_values("weight", ascending=False).drop_duplicates("soc2020").set_index("soc2020")

    # ISCO shares per SOC 2020 from the coding index, for the weighted exposure.
    idx = pd.read_excel(raw / "soc_coding_index" / "soc2020_coding_index.xlsx", sheet_name="SOC2020 coding index",
                        dtype=str, usecols=["SOC_2020", "ISCO-08 code based on SOC2020"])
    idx.columns = ["soc2020", "isco08"]
    idx = idx.dropna()
    idx = idx[idx.soc2020.str.fullmatch(r"\d{4}") & idx.isco08.str.fullmatch(r"\d{4}")]
    isco = idx.groupby(["soc2020", "isco08"]).size().rename("n").reset_index()
    isco["share"] = isco.n / isco.groupby("soc2020").n.transform("sum")
    isco = isco.merge(ilo, on="isco08", how="left")

    now = ft[ft.year == 2025].set_index("soc_code")
    titles = now["title"].to_dict()

    # COVID: all employees, SOC 2010, 2019 -> 2020, relative to the median occupation.
    w10 = allemp[allemp.soc_version == 2010].pivot_table(index="soc_code", columns="year", values="jobs_k")
    covid10 = np.log(w10[2020] / w10[2019]).replace([np.inf, -np.inf], np.nan).dropna()
    covid_base = float(covid10.median())
    covid_rel = (covid10 - covid_base).rename("rel").reset_index().rename(columns={"soc_code": "soc2010"})
    covid20 = comp.merge(covid_rel, on="soc2010")
    covid20 = covid20[covid20.weight > 0].assign(wx=lambda d: d.weight * d.rel)
    cs = covid20.groupby("soc2020")[["wx", "weight"]].sum()
    covid_by_soc = (cs.wx / cs.weight)

    # Cost of living: real median pay 2021 -> 2023, SOC 2020 native, relative to the median.
    w20 = ft[ft.soc_version == 2020].pivot_table(index="soc_code", columns="year", values="median")
    col = np.log((w20[2023] / cpi[2023]) / (w20[2021] / cpi[2021])).dropna()
    col_base = float(col.median())

    occupations, history, hedges = [], {}, {}
    for soc, short in DEMO.items():
        r = now.loc[soc]
        conf, cvflags = cv_conf(r["median_cv"])
        base_flags = ["employees_only", "provisional"] + cvflags
        g = series[series.soc2020 == soc].set_index("year").sort_index()
        dom_share = float(dominant.loc[soc, "weight"]) if soc in dominant.index else 0.0
        m = {}
        m["pay_median"] = metric(r["median"], "GBP/year", 2025, "ons_ashe_t14", "Median gross annual pay, full-time employees; range is the 25th to 75th percentile.",
                                 low=r["p25"], high=r["p75"], confidence=conf, flags=base_flags, nd=0)
        m["pay_p10"] = metric(r["p10"], "GBP/year", 2025, "ons_ashe_t14", "10th percentile of gross annual pay, full-time employees.",
                              confidence=conf if pd.notna(r["p10"]) else "low", flags=base_flags + ([] if pd.notna(r["p10"]) else ["suppressed"]), nd=0)
        m["pay_p90"] = metric(r["p90"], "GBP/year", 2025, "ons_ashe_t14", "90th percentile of gross annual pay, full-time employees (a ceiling).",
                              confidence=conf if pd.notna(r["p90"]) else "low", flags=base_flags + ([] if pd.notna(r["p90"]) else ["suppressed"]), nd=0)
        rp15 = g.loc[2015, "real"] if 2015 in g.index else np.nan
        rp25 = g.loc[2025, "real"] if 2025 in g.index else np.nan
        m["real_pay_change_10y"] = metric(rp25 / rp15 - 1 if rp15 else np.nan, "fraction", "2015-2025", "ons_ashe_t14",
                                          "Real change in median full-time pay, 2015 to 2025, in April 2025 prices (CPIH).",
                                          confidence="medium" if dom_share >= 0.8 else "low", flags=["bridged_soc2010", "employees_only", "provisional"])
        m["jobs"] = metric(r["jobs_k"], "thousand jobs", 2025, "ons_ashe_t14", "Full-time employee jobs (ASHE estimate).",
                           confidence="medium" if pd.notna(r["jobs_k"]) else "low", flags=base_flags + ([] if pd.notna(r["jobs_k"]) else ["suppressed"]), nd=1)
        t = theil(range(2021, 2026), [g.loc[y, "jobs_k"] if y in g.index else np.nan for y in range(2021, 2026)])
        m["demand_trend"] = metric(t[0] if t else None, "fraction/year", "2021-2025", "ons_ashe_t14",
                                   "Robust (Theil-Sen) yearly trend in full-time employee jobs since the 2021 code change; range is a 90% interval.",
                                   low=t[1] if t else None, high=t[2] if t else None, confidence=trend_conf(t[2] - t[1]) if t else "low",
                                   flags=["employees_only", "provisional"] + ([] if t else ["suppressed"]))
        t0 = theil(range(2011, 2020), [g.loc[y, "jobs_k"] if y in g.index else np.nan for y in range(2011, 2020)])
        m["demand_trend_2011_19"] = metric(t0[0] if t0 else None, "fraction/year", "2011-2019", "ons_ashe_t14",
                                           "Robust yearly trend in full-time employee jobs in the previous code era, bridged to today's code; range is a 90% interval.",
                                           low=t0[1] if t0 else None, high=t0[2] if t0 else None,
                                           confidence=(trend_conf(t0[2] - t0[1]) if dom_share >= 0.8 else "low") if t0 else "low",
                                           flags=["bridged_soc2010", "employees_only", "provisional"])
        e = isco[(isco.soc2020 == soc) & isco.exposure_mean.notna()]
        if len(e):
            wts = e.share / e.share.sum()
            mean = float((wts * e.exposure_mean).sum())
            sd = float(np.sqrt((wts * (e.exposure_mean - mean) ** 2).sum()))
            top = e.loc[e.share.idxmax()]
            m["exposure"] = metric(mean, "score 0-1", 2025, "ilo_wp140",
                                   "Generative-AI exposure of the occupation's tasks (ILO), averaged over the international codes its job titles map to; range shows their spread.",
                                   low=max(0.0, mean - sd), high=min(1.0, mean + sd),
                                   confidence="high" if sd <= 0.05 else "medium" if sd <= 0.10 else "low",
                                   flags=["multi_isco"] if len(e) > 1 else [],
                                   extra={"gradient": top["gradient"], "dominant_isco": top["isco08"], "n_isco": int(len(e))})
        else:
            m["exposure"] = metric(None, "score 0-1", 2025, "ilo_wp140", "No ILO score for this occupation's codes.", confidence="low", flags=["suppressed"])
        m["exposure_uk"] = metric(None, "score 0-1", 2023, "dfe_ai_uk_2023", "UK cross-check of AI exposure by SOC 2020 (DfE). Not loaded yet.",
                                  confidence="low", flags=["pending_source"], status="pending")
        cv = covid_by_soc.get(soc, np.nan)
        m["resilience_covid"] = metric(math.expm1(cv) if pd.notna(cv) else None, "fraction", "2019-2020", "ons_ashe_t14",
                                       "Change in all-employee jobs from 2019 to 2020 compared with the typical occupation (+0.10 = 10 points better).",
                                       confidence="low" if (pd.isna(cv) or abs(cv) > 0.4) else "medium",
                                       flags=["covid_year", "bridged_soc2010", "employees_only"])
        cl = col.get(soc, np.nan)
        m["resilience_cost_of_living"] = metric(math.expm1(cl - col_base) if pd.notna(cl) else None, "fraction", "2021-2023", "ons_ashe_t14",
                                                "Real pay change from 2021 to 2023 compared with the typical occupation (+0.05 = 5 points better).",
                                                confidence="medium" if pd.notna(cl) else "low", flags=["employees_only"])
        m["resilience_tech_slump"] = metric(None, "fraction", "2022-2024", "ons_online_job_adverts", "Change in online job adverts 2022 to 2024 vs all occupations. Not loaded yet.",
                                            confidence="low", flags=["pending_source"], status="pending")
        m["resilience_2008"] = metric(None, "fraction", "2008-2010", "ons_ashe_t14", "Jobs change 2008 to 2010 vs all occupations (needs ASHE 2007-2011, SOC 2000). Not loaded yet.",
                                      confidence="low", flags=["pending_source"], status="pending")
        occupations.append({"soc2020": soc, "title": titles.get(soc, short), "short_title": short,
                            "isco08": [{"code": c, "share": round(float(s), 4)} for c, s in
                                       isco[isco.soc2020 == soc].sort_values("share", ascending=False)[["isco08", "share"]].itertuples(index=False)],
                            "in_demo_set": True, "metrics": m})
        pts = []
        for y in range(2011, 2026):
            if y not in g.index:
                continue
            flags = []
            if y <= 2020:
                flags.append("bridged_soc2010")
            if y == 2020:
                flags.append("covid_year")
            if y in (2018, 2025):
                flags.append("provisional")
            if y >= 2021:
                flags.append("recoded_2021")
            pts.append({"year": y, "pay_median": num(g.loc[y, "median"], 0), "pay_median_real": num(g.loc[y, "real"], 0),
                        "jobs_k": num(g.loc[y, "jobs_k"], 1), "flags": flags})
        history[soc] = pts

    # Placeholder hedges: same 2-digit group first, then lower exposure.
    expo = {o["soc2020"]: o["metrics"]["exposure"]["value"] or 1.0 for o in occupations}
    for soc in DEMO:
        cands = []
        for other in DEMO:
            if other == soc:
                continue
            sim = 0.8 if other[:2] == soc[:2] else 0.6 if other[:1] == soc[:1] else 0.3
            cands.append((sim, -expo[other], other))
        cands.sort(reverse=True)
        hedges[soc] = [{"soc2020": o, "title": titles.get(o, DEMO[o]), "similarity": round(s, 2), "shared_skills": [],
                        "why": "Placeholder until ESCO skill overlap is computed (M3).", "status": "mock"} for s, _, o in cands[:5]]

    # Backtest: two native SOC 2010 windows and one bridged pay-only window.
    wp = ft[ft.soc_version == 2010].pivot_table(index="soc_code", columns="year", values="median")
    wj = ft[ft.soc_version == 2010].pivot_table(index="soc_code", columns="year", values="jobs_k")
    windows, spearman = [], {}
    for base in (2013, 2014):
        end = base + 5
        d = pd.DataFrame({"pay": wp[base], "prior": np.log(wj[base] / wj[2011]),
                          "rpg": np.log((wp[end] / cpi[end]) / (wp[base] / cpi[base])),
                          "jg": np.log(wj[end] / wj[base])}).replace([np.inf, -np.inf], np.nan).dropna()
        amb = d.pay >= d.pay.quantile(2 / 3)
        safe = d.prior >= d.prior.quantile(2 / 3)
        spearman[str(base)] = {"pay_level_vs_later_real_pay_growth": round(float(d[["pay", "rpg"]].corr("spearman").iloc[0, 1]), 3),
                               "prior_jobs_growth_vs_later_jobs_growth": round(float(d[["prior", "jg"]].corr("spearman").iloc[0, 1]), 3)}

        def group(key, label, mask):
            sub = d[mask]
            rp, jg = boot(sub.rpg), boot(sub.jg)
            return {"key": key, "label": label, "n": int(len(sub)),
                    "real_pay_growth": {"median": num(math.expm1(rp[0])), "low": num(math.expm1(rp[1])), "high": num(math.expm1(rp[2]))},
                    "jobs_growth": {"median": num(math.expm1(jg[0])), "low": num(math.expm1(jg[1])), "high": num(math.expm1(jg[2]))},
                    "share_jobs_fell": num(float((sub.jg < 0).mean()))}
        occ_rows = []
        for soc in DEMO:
            src = dominant.loc[soc, "soc2010"] if soc in dominant.index else None
            if src in d.index:
                gthen = "ambitious" if amb.get(src, False) else "safe" if safe.get(src, False) else "other"
                occ_rows.append({"soc2020": soc, "group_then": gthen, "real_pay_growth": num(math.expm1(d.loc[src, "rpg"])),
                                 "jobs_growth": num(math.expm1(d.loc[src, "jg"])), "flags": ["bridged_soc2010"]})
        windows.append({"base_year": base, "outcome_year": end, "horizon": 5, "coding": "SOC 2010 native", "flags": [], "jobs_comparable": True,
                        "groups": [group("ambitious", "Ambitious then: top third by pay", amb),
                                   group("safe", "Safe then: top third by prior jobs growth (2011 on)", safe),
                                   None,
                                   group("all", "All occupations with complete data", d.pay.notna())],
                        "occupations": occ_rows})
    # Bridged window 2019 -> 2024: pay only, since job counts are not comparable across 2021.
    sp = series.pivot_table(index="soc2020", columns="year", values="real")
    sj = series[series.bridged].pivot_table(index="soc2020", columns="year", values="jobs_k")
    d = pd.DataFrame({"pay": sp[2019], "prior": np.log(sj[2019] / sj[2015]), "rpg": np.log(sp[2024] / sp[2019])}).replace([np.inf, -np.inf], np.nan).dropna()
    amb, safe = d.pay >= d.pay.quantile(2 / 3), d.prior >= d.prior.quantile(2 / 3)

    def pay_group(key, label, mask):
        rp = boot(d[mask].rpg)
        return {"key": key, "label": label, "n": int(mask.sum()),
                "real_pay_growth": {"median": num(math.expm1(rp[0])), "low": num(math.expm1(rp[1])), "high": num(math.expm1(rp[2]))},
                "jobs_growth": None, "share_jobs_fell": None}
    windows.append({"base_year": 2019, "outcome_year": 2024, "horizon": 5, "coding": "bridged SOC 2010 -> SOC 2020",
                    "flags": ["bridged_soc2010", "covid_year", "recoded_2021"], "jobs_comparable": False,
                    "groups": [pay_group("ambitious", "Ambitious then: top third by pay", amb),
                               pay_group("safe", "Safe then: top third by prior jobs growth (2015-19)", safe),
                               None, pay_group("all", "All occupations with complete data", d.pay.notna())],
                    "occupations": [{"soc2020": soc, "group_then": "ambitious" if amb.get(soc, False) else "safe" if safe.get(soc, False) else "other",
                                     "real_pay_growth": num(math.expm1(d.loc[soc, "rpg"])), "jobs_growth": None,
                                     "flags": ["bridged_soc2010", "covid_year"]} for soc in DEMO if soc in d.index]})

    # Bridge seam check for eval.json.
    s20 = series[(series.year == 2020) & series.bridged].set_index("soc2020")
    s21 = series[(series.year == 2021) & ~series.bridged].set_index("soc2020")
    seam = {}
    for c in ("median", "jobs_k"):
        rr = (s21[c] / s20[c]).replace([np.inf, -np.inf], np.nan).dropna()
        seam[c] = {"n": int(len(rr)), "median_ratio": num(rr.median(), 3), "iqr": [num(rr.quantile(.25), 3), num(rr.quantile(.75), 3)],
                   "share_outside_0.8_1.25": num(float(((rr < 0.8) | (rr > 1.25)).mean()), 3)}

    meta = {"schema_version": "1.0", "generated_at": NOW}
    write(out, "occupations", {**meta, "status": "preliminary", "price_base": "CPIH, April 2025 prices", "demo_set": list(DEMO), "occupations": occupations})
    write(out, "history", {**meta, "status": "preliminary", "occupations": history})
    write(out, "hedges", {**meta, "status": "mock", "method": "placeholder: same SOC group first, then lower exposure", "occupations": hedges})
    write(out, "fit", {**meta, "status": "mock", "method": "hand-assigned placeholder affinities",
                       "tags": [{"id": t, "label": lbl, "keywords": kws} for t, lbl, kws in TAGS], "affinity": AFFINITY})
    write(out, "backtest", {**meta, "status": "preliminary",
                            "method": "Pre-registered naive tiers, nothing tuned to outcomes. Ambitious: top third by pay at the base year. Safe: top third by prior jobs growth. Outcomes 5 years later; real pay in CPIH-deflated terms.",
                            "caveats": ["Historical tiers use market data only: no historical AI exposure index exists.",
                                        "Windows overlap, so they are not independent.",
                                        "Only occupations with complete data are included (larger occupations).",
                                        "Low-pay occupations gained from minimum-wage rises after 2016, which lowers the Ambitious group's relative pay growth.",
                                        "Windows crossing 2021 compare pay only; job counts are not comparable across the code change.",
                                        "The 2019-2024 window includes the 2020 COVID year."],
                            "windows": windows})
    write(out, "crises", {**meta, "status": "preliminary", "crises": [
        {"key": "covid", "label": "COVID-19", "window": "2019-2020", "measure": "All-employee jobs, log change", "baseline_median": num(math.expm1(covid_base)), "status": "preliminary", "flags": ["covid_year", "bridged_soc2010"]},
        {"key": "cost_of_living", "label": "Cost-of-living shock", "window": "2021-2023", "measure": "Real median full-time pay", "baseline_median": num(math.expm1(col_base)), "status": "preliminary", "flags": []},
        {"key": "tech_slump", "label": "Tech hiring slump", "window": "2022-2024", "measure": "Online job adverts", "baseline_median": None, "status": "pending", "flags": ["pending_source"]},
        {"key": "gfc_2008", "label": "2008 financial crisis", "window": "2008-2010", "measure": "Employee jobs", "baseline_median": None, "status": "pending", "flags": ["pending_source"]}]})
    write(out, "sources", {**meta, "status": "preliminary", "sources": SOURCES})
    write(out, "eval", {**meta, "status": "preliminary", "checks": {
        "bridge_seam": {"status": "preliminary", "date": NOW[:10], "summary": "Bridged 2020 vs native 2021: pay lines up, job counts do not.", "metrics": seam},
        "backtest_probe": {"status": "preliminary", "date": NOW[:10], "summary": "Spearman correlations in the two native windows.", "metrics": spearman},
        "matcher": {"status": "pending", "date": None, "summary": "Keyword vs zero-shot vs fine-tuned on held-out human labels (needs ESCO and labels).", "metrics": {}},
        "exposure_agreement": {"status": "pending", "date": None, "summary": "ILO vs DfE vs in-house task labels.", "metrics": {}},
        "hedge_sanity": {"status": "pending", "date": None, "summary": "ESCO skill overlap vs O*NET related occupations.", "metrics": {}}}})
    print(f"wrote {len(occupations)} occupations, {len(windows)} backtest windows to {out}")


if __name__ == "__main__":
    main()
