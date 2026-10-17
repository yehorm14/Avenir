"""Shared constants and helpers for the ML build scripts (contract v1.1)."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

SCHEMA_VERSION = "1.1"
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

# Placeholder affinities (status "mock") until the matcher (M1) is evaluated on human labels.
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

OGL = "Open Government Licence v3.0"
SOURCES = {
    "ons_ashe_t14": {"name": "Annual Survey of Hours and Earnings, Table 14 (occupation by 4-digit SOC)", "publisher": "ONS",
                     "url": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14",
                     "licence": OGL, "coverage": "UK employees; excludes self-employed", "years": "2007-2025", "status": "loaded",
                     "notes": "SOC 2000 to 2010, SOC 2010 2011-2020, SOC 2020 from 2021; 2018 and 2025 provisional"},
    "ons_cpih": {"name": "CPIH index (L522)", "publisher": "ONS", "url": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23",
                 "licence": OGL, "coverage": "UK", "years": "1988-2026", "status": "loaded", "notes": "April values, the ASHE reference month"},
    "ons_soc_crosswalk": {"name": "Relationship between SOC 2010 and SOC 2020 (July 2021)", "publisher": "ONS",
                          "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/therelationshipbetweenstandardoccupationalclassification2010andstandardoccupationalclassification2020",
                          "licence": OGL, "coverage": "LFS 2014-16 and Census 2011 dual coding", "years": "2021", "status": "loaded", "notes": "Bridges 2011-2020 data"},
    "ons_soc_crosswalk_2000": {"name": "Relationship between SOC 2010 and SOC 2000", "publisher": "ONS",
                               "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2010",
                               "licence": OGL, "coverage": "LFS Jan-Mar 2007 and Census 2001 dual coding", "years": "2010", "status": "loaded", "notes": "Bridges 2007-2010 data"},
    "ons_soc_coding_index": {"name": "SOC 2020 Volume 2: the coding index", "publisher": "ONS",
                             "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions",
                             "licence": OGL, "coverage": "About 32,000 UK job titles", "years": "2026", "status": "loaded", "notes": "Job title to SOC 2020 and ISCO-08"},
    "ilo_wp140": {"name": "Generative AI and Jobs: A Refined Global Index of Occupational Exposure (Working Paper 140)", "publisher": "ILO",
                  "url": "https://webapps.ilo.org/static/english/intserv/working-papers/wp140/index.html",
                  "licence": "To confirm before public release", "coverage": "427 ISCO-08 occupations", "years": "2025", "status": "loaded", "notes": "Mean task exposure and its spread"},
    "dfe_ai_uk_2023": {"name": "The impact of AI on UK jobs and training, Annex 1", "publisher": "Department for Education",
                       "url": "https://www.gov.uk/government/publications/the-impact-of-ai-on-uk-jobs-and-training",
                       "licence": OGL, "coverage": "365 SOC 2010 occupations (AIOE, LLM exposure)", "years": "2023", "status": "loaded", "notes": "UK cross-check, used as a percentile rank"},
    "ons_online_job_adverts": {"name": "Online job advert estimates (source: Adzuna)", "publisher": "ONS",
                               "url": "https://www.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/onlinejobadvertestimates",
                               "licence": OGL, "coverage": "28 job-advert categories, weekly", "years": "2018-2024", "status": "loaded", "notes": "Discontinued October 2024; category level only"},
    "ons_aps_2016_age": {"name": "4-digit occupation by age bands, Annual Population Survey 2016 (ad hoc 006998)", "publisher": "ONS",
                         "url": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/adhocs/0069984digitoccupationsocand4digitindustrysicbyagebands",
                         "licence": OGL, "coverage": "UK, includes self-employed", "years": "2016", "status": "loaded", "notes": "SOC 2010; small cells suppressed"},
    "esco": {"name": "ESCO v1.2.1 classification", "publisher": "European Commission", "url": "https://esco.ec.europa.eu/",
             "licence": "EU open data (attribution)", "coverage": "3,043 occupations, 13,939 skills", "years": "2025", "status": "loaded", "notes": "Skills for hedges"},
    "onet": {"name": "O*NET 31.0 related occupations and the ESCO to O*NET-SOC crosswalk", "publisher": "US Department of Labor (O*NET)",
             "url": "https://www.onetcenter.org/database.html", "licence": "CC BY 4.0", "coverage": "US occupations", "years": "2026",
             "status": "loaded", "notes": "Reference check of hedges only"},
    "census_occupation": {"name": "Census 2011 and 2021 occupation (England and Wales); Scotland 2011 and 2022", "publisher": "ONS / NRS",
                          "url": "https://www.nomisweb.co.uk/", "licence": OGL, "coverage": "Includes self-employed",
                          "years": "2011, 2021/2022", "status": "pending", "notes": "Self-employed coverage (not loaded yet)"},
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


def theil(years, values, min_points=4):
    years, values = np.asarray(years, float), np.asarray(values, float)
    ok = np.isfinite(values) & (values > 0)
    if ok.sum() < min_points:
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


def weighted_map(values: pd.Series, weights: pd.DataFrame, src: str, dst: str, wcol: str = "weight") -> pd.DataFrame:
    """Map values keyed by `src` codes onto `dst` codes as a weighted mean (weights renormalised
    over sources that have a value). Returns dst, value, coverage (share of weight with a value)
    and dominant (largest single weight)."""
    w = weights[weights[wcol] > 0][[dst, src, wcol]]
    total = w.groupby(dst)[wcol].sum()
    dominant = w.groupby(dst)[wcol].max()
    m = w.merge(values.rename("v").reset_index().rename(columns={values.index.name or "index": src}), on=src).dropna(subset=["v"])
    m["wx"] = m[wcol] * m["v"]
    s = m.groupby(dst)[["wx", wcol]].sum()
    out = pd.DataFrame({"value": s.wx / s[wcol], "coverage": s[wcol] / total.reindex(s.index)})
    out["dominant"] = dominant.reindex(out.index)
    return out


def write(out_dir: Path, name: str, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
