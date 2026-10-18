"""Shared constants and helpers for the ML build scripts (contract v1.2)."""
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

SCHEMA_VERSION = "1.2"
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

# Keyword syntax (see pathfinder_ml.api.match_tags): a trailing * means prefix match; otherwise the
# whole word with an optional plural; spaces match any whitespace or hyphen.
TAGS = [
    ("maths", "Maths and numbers", ["math*", "numbers", "algebra", "calculus", "equation*", "statistic*", "probability"]),
    ("art_drawing", "Art and drawing", ["draw*", "art", "paint*", "sketch*", "illustrat*"]),
    ("design", "Design and visuals", ["design*", "layout*", "typograph*", "visual*", "graphic*", "ux"]),
    ("computers_coding", "Computers and coding", ["code", "coding", "program*", "software", "computer*", "apps", "python", "developer"]),
    ("data", "Data and spreadsheets", ["data", "spreadsheet*", "excel", "analys*", "chart*", "trend*", "pattern*"]),
    ("building_spaces", "Buildings and spaces", ["building*", "architect*", "house*", "interior*", "cities", "construction", "spaces"]),
    ("engineering_making", "Engineering and making things", ["engineer*", "make things", "making things", "build things", "building things", "lego", "robot*", "machine*", "mechanical"]),
    ("fixing_hands_on", "Fixing things, hands-on", ["fix*", "repair*", "hands on", "tools", "wiring", "bike*", "practical", "taking things apart"]),
    ("electricity_energy", "Electricity and energy", ["electric*", "electronic*", "circuit*", "energy", "solar", "power supply", "batteries"]),
    ("science_health", "Science and health", ["biology", "medicine", "medical", "health*", "hospital*", "physics", "science", "scientific"]),
    ("helping_people", "Helping people", ["help* people", "helping", "caring", "care for", "patient*", "community", "support* people"]),
    ("teaching_explaining", "Teaching and explaining", ["teach*", "explain*", "tutor*", "coach*", "mentor*", "kids"]),
    ("money_business", "Money and business", ["money", "financ*", "invest*", "business*", "stock market", "stocks", "economic*", "trading", "accounts"]),
    ("security_puzzles", "Security and puzzles", ["security", "hacking", "hacker*", "cyber*", "puzzle*", "cipher*", "breach*"]),
    ("writing_language", "Writing and languages", ["writing", "writer", "language*", "english", "stories", "translat*"]),
    ("outdoors_maps", "Outdoors and maps", ["outdoor*", "map*", "geograph*", "landscape*", "survey*", "measuring"]),
]

# Placeholder affinities (status "mock"); replaced by m1_matcher build-fit.
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
OGL_ATTR = "Contains public sector information licensed under the Open Government Licence v3.0."
SOURCES = {
    "ons_ashe_t14": {"name": "Annual Survey of Hours and Earnings, Table 14 (occupation by 4-digit SOC)", "publisher": "ONS",
                     "url": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14",
                     "licence": OGL, "attribution": OGL_ATTR,
                     "coverage": "UK employees on adult rates who have been in the same job for over a year; excludes self-employed", "years": "2007-2025 (tax years ending 5 April)",
                     "status": "loaded",
                     "notes": "SOC 2000 to 2010, SOC 2010 2011-2020, SOC 2020 from 2021. 2018 and 2025 editions are provisional. ONS says job counts are indicative, not accurate estimates, and that 2021-22 are affected by occupation miscoding."},
    "ons_cpih": {"name": "CPIH index (L522)", "publisher": "ONS", "url": "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23",
                 "licence": OGL, "attribution": OGL_ATTR, "coverage": "UK", "years": "1988-2026", "status": "loaded",
                 "notes": "Tax-year means (April to March) deflate annual pay, matching the ASHE reference period"},
    "ons_soc_crosswalk": {"name": "Relationship between SOC 2010 and SOC 2020 (July 2021)", "publisher": "ONS",
                          "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/therelationshipbetweenstandardoccupationalclassification2010andstandardoccupationalclassification2020",
                          "licence": OGL, "attribution": OGL_ATTR, "coverage": "LFS 2014-16 and Census 2011 dual coding", "years": "2021", "status": "loaded", "notes": "Bridges 2011-2020 data"},
    "ons_soc_crosswalk_2000": {"name": "Relationship between SOC 2010 and SOC 2000", "publisher": "ONS",
                               "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2010",
                               "licence": OGL, "attribution": OGL_ATTR, "coverage": "LFS Jan-Mar 2007 and Census 2001 dual coding", "years": "2010", "status": "loaded", "notes": "Bridges 2007-2010 data"},
    "ons_soc_coding_index": {"name": "SOC 2020 Volume 2: the coding index", "publisher": "ONS",
                             "url": "https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions",
                             "licence": OGL, "attribution": OGL_ATTR, "coverage": "About 32,000 UK job titles", "years": "2026", "status": "loaded", "notes": "Job title to SOC 2020 and ISCO-08"},
    "ilo_wp140": {"name": "Generative AI and Jobs: A Refined Global Index of Occupational Exposure (Working Paper 140)", "publisher": "ILO",
                  "url": "https://webapps.ilo.org/static/english/intserv/working-papers/wp140/index.html",
                  "licence": "CC BY 4.0 (© ILO 2025)",
                  "attribution": "Adapted from ILO Working Paper 140, Gmyrek et al. (2025), https://doi.org/10.54394/HETP0387, CC BY 4.0. Changes made: scores were averaged over the international codes a UK occupation maps to. This is an adaptation of a copyrighted work of the International Labour Organization (ILO). This adaptation has not been prepared, reviewed or endorsed by the ILO and should not be considered an official ILO adaptation. The ILO disclaims all responsibility for its content and accuracy. Responsibility rests solely with the author(s) of the adaptation.",
                  "coverage": "427 ISCO-08 occupations", "years": "2025", "status": "loaded", "notes": "Mean task exposure and its spread per occupation"},
    "dfe_ai_uk_2023": {"name": "The impact of AI on UK jobs and training, Annex 1", "publisher": "Department for Education",
                       "url": "https://www.gov.uk/government/publications/the-impact-of-ai-on-uk-jobs-and-training",
                       "licence": OGL, "attribution": OGL_ATTR, "coverage": "365 SOC 2010 occupations (AIOE, LLM exposure)", "years": "2023", "status": "loaded", "notes": "UK cross-check, used as a percentile rank"},
    "ons_online_job_adverts": {"name": "Online job advert estimates (source: Adzuna)", "publisher": "ONS",
                               "url": "https://www.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/onlinejobadvertestimates",
                               "licence": OGL, "attribution": OGL_ATTR + " Underlying adverts: Adzuna.", "coverage": "28 job-advert categories, weekly, de-duplicated series", "years": "2018-2024", "status": "loaded",
                               "notes": "Discontinued October 2024; category level only; ONS flags Education, Marketing/PR, Transport and Travel as inconsistent in 2023"},
    "ons_aps_2016_age": {"name": "4-digit occupation by age bands, Annual Population Survey 2016 (ad hoc 006998)", "publisher": "ONS",
                         "url": "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/adhocs/0069984digitoccupationsocand4digitindustrysicbyagebands",
                         "licence": OGL, "attribution": OGL_ATTR, "coverage": "UK, includes self-employed", "years": "2016", "status": "loaded", "notes": "SOC 2010; small cells suppressed"},
    "esco": {"name": "ESCO v1.2.1 classification", "publisher": "European Commission", "url": "https://esco.ec.europa.eu/",
             "licence": "EU open data (attribution)", "attribution": "ESCO © European Union, 2025. Used under the ESCO terms of use.",
             "coverage": "3,039 occupations, 13,939 skills", "years": "2025", "status": "loaded", "notes": "Skills for hedges and the matcher's career texts"},
    "onet": {"name": "O*NET 31.0 related occupations and the ESCO to O*NET-SOC crosswalk", "publisher": "US Department of Labor (O*NET)",
             "url": "https://www.onetcenter.org/database.html", "licence": "CC BY 4.0",
             "attribution": "This product uses the O*NET 31.0 database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), under CC BY 4.0. O*NET is a trademark of USDOL/ETA.",
             "coverage": "US occupations", "years": "2026", "status": "loaded", "notes": "Reference check of hedges only"},
    "census_occupation": {"name": "Census 2011 and 2021 occupation (England and Wales); Scotland 2011 and 2022", "publisher": "ONS / NRS",
                          "url": "https://www.nomisweb.co.uk/", "licence": OGL, "attribution": OGL_ATTR, "coverage": "Includes self-employed",
                          "years": "2011, 2021/2022", "status": "pending", "notes": "Self-employed coverage (not loaded yet)"},
}

# Confidence policy (contract 2.4). Applied to every metric after it is built.
CAP_LOW = {"mock", "cv_high", "imputed_parent", "bridged_low_purity", "partial_sources", "suppressed", "pending_source"}
CAP_MEDIUM = {"bridged_soc2010", "bridged_soc2000", "multi_isco", "category_level", "covid_year", "ons_indicative_counts",
              "sources_disagree", "fallback_all_employees"}
NO_CAP = {"employees_only", "provisional", "recoded_2021"}
ORDER = {"low": 0, "medium": 1, "high": 2}


def cap_confidence(metric: dict) -> dict:
    """Enforce the contract's confidence rule on a built metric, in place, and return it."""
    conf = metric.get("confidence", "medium")
    flags = set(metric.get("flags", []))
    if metric.get("value") is None or flags & CAP_LOW:
        conf = "low"
    elif flags & CAP_MEDIUM and ORDER[conf] > ORDER["medium"]:
        conf = "medium"
    metric["confidence"] = conf
    return metric


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
    flags = set(flags)
    value_n = num(value, nd)
    if value_n is None and status != "pending":
        flags.add("suppressed")
    low_n, high_n = num(low, nd), num(high, nd)
    if (low_n is None) != (high_n is None):  # ranges are two-sided or absent
        low_n = high_n = None
    m = {"value": value_n, "low": low_n, "high": high_n, "unit": unit, "as_of": str(as_of),
         "source": source, "granularity": granularity, "confidence": confidence, "flags": sorted(flags),
         "status": status, "note": note, "extra": extra or {}}
    return cap_confidence(m)


def cv_conf(cv):
    if cv is None or (isinstance(cv, float) and math.isnan(cv)):
        return "low", []
    if cv <= 5:
        return "high", []
    if cv <= 10:
        return "medium", []
    return "low", ["cv_high"]


def cpih_monthly(path: Path) -> pd.Series:
    df = pd.read_csv(path, header=None, names=["period", "value"])
    df = df[df["period"].astype(str).str.fullmatch(r"\d{4} [A-Z]{3}")]
    idx = pd.to_datetime(df["period"], format="%Y %b")
    return pd.Series(df["value"].astype(float).values, index=idx).sort_index()


def cpih_taxyear(path: Path) -> dict:
    """Mean CPIH over the tax year ending 5 April of each year (April Y-1 to March Y): the period
    ASHE annual pay refers to. Falls back to the April value for years with incomplete months."""
    m = cpih_monthly(path)
    out = {}
    for y in range(1990, 2030):
        window = m[(m.index >= f"{y - 1}-04-01") & (m.index <= f"{y}-03-31")]
        if len(window) == 12:
            out[y] = float(window.mean())
        elif f"{y}-04-01" in m.index.strftime("%Y-%m-%d"):
            out[y] = float(m[f"{y}-04-01"])
    return out


def theil(years, values, min_points=4):
    years, values = np.asarray(years, float), np.asarray(values, float)
    ok = np.isfinite(values) & (values > 0)
    if ok.sum() < min_points:
        return None
    slope, _, lo, hi = theilslopes(np.log(values[ok]), years[ok], alpha=0.90)
    return math.expm1(slope), math.expm1(lo), math.expm1(hi)


def trend_conf(width):
    return "high" if width <= 0.08 else "medium" if width <= 0.20 else "low"


def boot(values, n=2000, rng=None):
    rng = rng or np.random.default_rng(0)
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if len(values) < 5:
        return None, None, None
    draws = np.median(rng.choice(values, size=(n, len(values)), replace=True), axis=1)
    return float(np.median(values)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def weighted_map(values: pd.Series, weights: pd.DataFrame, src: str, dst: str, wcol: str = "weight") -> pd.DataFrame:
    """Map values keyed by `src` codes onto `dst` codes as a weighted mean (weights renormalised
    over sources that have a value). Returns dst -> value, coverage (share of weight with a value)
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
    """Atomic JSON write (temp file then replace), LF line endings, no NaN tokens."""
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=1, ensure_ascii=False, allow_nan=False) + "\n"
    tmp = out_dir / f".{name}.json.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, out_dir / f"{name}.json")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else None


def assign_tiers(base: pd.DataFrame) -> pd.DataFrame:
    """Backtest tiers from base-year features only (columns pay, prior). Cutoffs are thirds of the
    base-year population; outcomes are attached afterwards, so a missing future value can never move
    another occupation between tiers (no look-ahead, AGENTS rule 6)."""
    base = base[["pay", "prior"]].dropna()
    return pd.DataFrame({"ambitious": base.pay >= base.pay.quantile(2 / 3),
                         "safe": base.prior >= base.prior.quantile(2 / 3)}, index=base.index)
