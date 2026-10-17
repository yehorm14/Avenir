"""Builds the demo snapshots that have no hand-written equivalent yet:

  regions.json   sector demand multipliers per UK nation and English region
  nations.json   apprenticeship and study routes for Scotland, Wales and Northern Ireland
  backtest.json  SYNTHETIC past-year signal inputs and outcomes for the self-grade

Every file is marked as demo data. backtest.json in particular is not a track
record: it is generated here so the backtest engine and the "pick a past year"
replay can be built and tested before the real ESS 2011-2019, Working Futures
and LFS/ASHE series are loaded. The generator parameters are written into the
file so nobody can mistake it for evidence.

  ashe_series.json  SYNTHETIC 2015-2025 pay history (median and middle half) per occupation, anchored to ashe.json
  cpi.json          Approximate UK CPI annual averages, 2015 = 100 (verify against ONS series D7BT)

Run:  ../.conda/bin/python scripts/build_demo_snapshots.py   (from backend/)
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"


def load(name: str) -> dict:
    return json.loads((SNAP / name).read_text())


def dump(name: str, data: dict) -> None:
    (SNAP / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- regions ----

SECTORS = [
    "Digital and technologies", "Advanced manufacturing", "Construction", "Clean energy",
    "Health and social care", "Education", "Professional and business services",
    "Creative industries", "Hospitality", "Life sciences", "Public services", "Financial services",
]

# Relative to the UK average (1.0). Demo values shaped like the regional
# assessments: London over-indexes on digital and professional services,
# Scotland and the North East on clean energy, and so on.
REGION_MULTIPLIERS = {
    "UK-wide": {},
    "Scotland": {"Financial services": 1.1, "Clean energy": 1.3, "Health and social care": 1.1, "Life sciences": 1.1, "Digital and technologies": 0.95, "Professional and business services": 0.9},
    "Wales": {"Advanced manufacturing": 1.15, "Health and social care": 1.15, "Clean energy": 1.15, "Digital and technologies": 0.85, "Professional and business services": 0.85},
    "Northern Ireland": {"Digital and technologies": 1.1, "Advanced manufacturing": 1.15, "Professional and business services": 0.95, "Creative industries": 0.9},
    "North East": {"Financial services": 0.8, "Clean energy": 1.3, "Advanced manufacturing": 1.2, "Digital and technologies": 0.85, "Professional and business services": 0.85},
    "North West": {"Advanced manufacturing": 1.1, "Digital and technologies": 1.05, "Health and social care": 1.05},
    "Yorkshire and the Humber": {"Clean energy": 1.2, "Advanced manufacturing": 1.1, "Digital and technologies": 0.9},
    "East Midlands": {"Advanced manufacturing": 1.2, "Construction": 1.05, "Digital and technologies": 0.85},
    "West Midlands": {"Advanced manufacturing": 1.25, "Construction": 1.1, "Digital and technologies": 0.95},
    "East of England": {"Life sciences": 1.3, "Construction": 1.1, "Digital and technologies": 1.0},
    "London": {"Financial services": 1.4, "Digital and technologies": 1.3, "Professional and business services": 1.3, "Creative industries": 1.3, "Hospitality": 1.15, "Advanced manufacturing": 0.7, "Clean energy": 0.85},
    "South East": {"Life sciences": 1.15, "Digital and technologies": 1.1, "Construction": 1.1},
    "South West": {"Clean energy": 1.1, "Hospitality": 1.15, "Advanced manufacturing": 1.05, "Digital and technologies": 0.9},
}
REGION_SOURCE = {
    "Scotland": "sds_rsa", "Wales": "regional_wales", "Northern Ireland": "regional_ni",
}


def build_regions() -> dict:
    regions = {}
    for name, m in REGION_MULTIPLIERS.items():
        nation = name if name in ("Scotland", "Wales", "Northern Ireland") else ("UK" if name == "UK-wide" else "England")
        regions[name] = {
            "nation": nation,
            "source_id": REGION_SOURCE.get(name, "oid" if nation == "England" else "skills_england"),
            "multipliers": {s: m.get(s, 1.0) for s in SECTORS},
        }
    return {
        "source_id": "regions",
        "edition": "2025-26 (demo snapshot)",
        "_note": "Sector demand multipliers relative to the UK average, applied to both demand signals before scaling. DEMO VALUES: to be derived from Occupations in Demand (England regions), SDS Regional Skills Assessments (Scotland), and the Welsh and Northern Ireland regional skills partnerships.",
        "regions": regions,
    }


# ---------------------------------------------------------------- nations ----

# Route families. Names follow each nation's frameworks; the exact framework
# titles and levels must be checked with apprenticeships.scot, Apprenticeships
# Wales and nidirect before use.
FAMILY = {
    "digital_degree": ["2134", "2135", "2425"],
    "it_support": ["3132"],
    "engineering": ["2122", "2123"],
    "civil": ["2121", "2453", "1122"],
    "business": ["2422", "2440", "3556", "3554"],
    "trade": ["5241", "5314", "5316", "5313", "5231"],
    "health_degree": ["2232", "2235", "2221", "2222", "2223", "2255", "2254", "2251"],
    "care": ["6135"],
    "teaching": ["2313", "2314"],
    "social_work": ["2461"],
    "psychology": ["2225"],
    "accounting": ["2421"],
    "law": ["2412"],
    "architecture": ["2451"],
    "design": ["3421"],
    "science": ["2152", "2113"],
    "chef": ["5434"],
    "vet": ["2240"],
    "police": ["3312"],
}

GA = {"2134": "Software Development", "2135": "Cyber Security", "2425": "Data Science",
      "2122": "Engineering: Design and Manufacture", "2123": "Engineering: Instrumentation, Measurement and Control",
      "2121": "Civil Engineering", "2453": "Construction and the Built Environment", "1122": "Construction and the Built Environment"}
MA = {"5241": "Electrical Installation", "5314": "Plumbing and Heating", "5316": "Construction: Building (Carpentry and Joinery)",
      "5313": "Construction: Building (Brickwork)", "5231": "Vehicle Maintenance and Repair"}


def scotland(soc: str, fam: str) -> list[dict]:
    r: list[dict] = []
    if fam == "digital_degree":
        r += [{"type": "Graduate Apprenticeship", "name": GA[soc], "level": "SCQF 9–10"},
              {"type": "Foundation Apprenticeship", "name": "IT: Software Development", "level": "SCQF 6, in S5–S6"}]
    elif fam == "it_support":
        r += [{"type": "Modern Apprenticeship", "name": "IT and Telecommunications", "level": "SCQF 6"},
              {"type": "Foundation Apprenticeship", "name": "IT: Hardware and System Support", "level": "SCQF 6, in S5–S6"}]
    elif fam in ("engineering", "civil"):
        r += [{"type": "Graduate Apprenticeship", "name": GA[soc], "level": "SCQF 9–10"},
              {"type": "Foundation Apprenticeship", "name": "Civil Engineering" if fam == "civil" else "Engineering", "level": "SCQF 6, in S5–S6"}]
    elif fam == "trade":
        r += [{"type": "Modern Apprenticeship", "name": MA[soc], "level": "SCQF 6–7"}]
    elif fam == "business":
        r += [{"type": "Graduate Apprenticeship", "name": "Business Management", "level": "SCQF 9–10"},
              {"type": "Foundation Apprenticeship", "name": "Business Skills", "level": "SCQF 6, in S5–S6"}]
    elif fam == "health_degree":
        r += [{"type": "University", "name": "Degree at a Scottish university (no degree apprenticeship route)", "level": "SCQF 9–10"},
              {"type": "Foundation Apprenticeship", "name": "Social Services and Healthcare", "level": "SCQF 6, in S5–S6"}]
    elif fam == "care":
        r += [{"type": "Modern Apprenticeship", "name": "Social Services and Healthcare", "level": "SCQF 6–7"},
              {"type": "Foundation Apprenticeship", "name": "Social Services and Healthcare", "level": "SCQF 6, in S5–S6"}]
    elif fam == "teaching":
        r += [{"type": "University", "name": "Degree, then a PGDE and a probation year", "level": "SCQF 9–11"}]
    elif fam == "social_work":
        r += [{"type": "University", "name": "Social work degree (BA)", "level": "SCQF 10"},
              {"type": "Foundation Apprenticeship", "name": "Social Services: Children and Young People", "level": "SCQF 6, in S5–S6"}]
    elif fam == "accounting":
        r += [{"type": "Modern Apprenticeship", "name": "Accounting", "level": "SCQF 6–8"},
              {"type": "Foundation Apprenticeship", "name": "Accountancy", "level": "SCQF 6, in S5–S6"}]
    elif fam == "law":
        r += [{"type": "University", "name": "LLB, then the Diploma in Professional Legal Practice", "level": "SCQF 10–11"}]
    elif fam == "design":
        r += [{"type": "Modern Apprenticeship", "name": "Creative and Digital Media", "level": "SCQF 6"},
              {"type": "Foundation Apprenticeship", "name": "Creative and Digital Media", "level": "SCQF 6, in S5–S6"}]
    elif fam == "science":
        r += [{"type": "Modern Apprenticeship", "name": "Life Sciences and Related Science Industries", "level": "SCQF 6–7"},
              {"type": "Foundation Apprenticeship", "name": "Scientific Technologies", "level": "SCQF 6, in S5–S6"}]
    elif fam == "chef":
        r += [{"type": "Modern Apprenticeship", "name": "Hospitality", "level": "SCQF 5–7"}]
    elif fam == "police":
        r += [{"type": "Direct entry", "name": "Police Scotland probationer training", "level": "Scottish Police College"}]
    else:  # psychology, architecture, vet: degree only
        r += [{"type": "University", "name": "Degree at a Scottish university", "level": "SCQF 9–11"}]
    return r


def wales(soc: str, fam: str) -> list[dict]:
    if fam in ("digital_degree", "engineering", "civil"):
        return [{"type": "Degree apprenticeship", "name": "Degree apprenticeship (digital or engineering, funded in Wales)", "level": "Level 6"},
                {"type": "Apprenticeship", "name": "Higher Apprenticeship via Apprenticeships Wales", "level": "Level 4–5"}]
    if fam in ("trade", "it_support", "care", "chef", "accounting", "design"):
        return [{"type": "Apprenticeship", "name": "Apprenticeship via Apprenticeships Wales", "level": "Level 2–3"}]
    if fam == "business":
        return [{"type": "Apprenticeship", "name": "Higher Apprenticeship via Apprenticeships Wales", "level": "Level 4–5"}]
    return [{"type": "University", "name": "Degree at a Welsh or other UK university (no degree apprenticeship in Wales)", "level": "Level 6"}]


def ni(soc: str, fam: str) -> list[dict]:
    if fam in ("trade", "it_support", "care", "chef", "design"):
        return [{"type": "Apprenticeship", "name": "ApprenticeshipsNI", "level": "Level 2–3"}]
    if fam in ("digital_degree", "engineering", "civil", "accounting", "science", "business"):
        return [{"type": "Higher Level Apprenticeship", "name": "Higher Level Apprenticeship (NI)", "level": "Level 4–6"}]
    return [{"type": "University", "name": "Degree at a Northern Ireland or other UK university", "level": "Level 6"}]


def build_nations() -> dict:
    soc_family = {soc: fam for fam, socs in FAMILY.items() for soc in socs}
    out = {}
    for soc, fam in soc_family.items():
        out[soc] = {"Scotland": scotland(soc, fam), "Wales": wales(soc, fam), "Northern Ireland": ni(soc, fam)}
    return {
        "source_id": "nations",
        "edition": "2026 (demo snapshot)",
        "_note": "Routes outside England: Modern, Foundation and Graduate Apprenticeships (Scotland, apprenticeships.scot), Apprenticeships Wales, ApprenticeshipsNI. DEMO SNAPSHOT: framework titles and levels to be confirmed with each nation's service.",
        "occupations": out,
    }


# --------------------------------------------------------------- backtest ----

YEARS = [2011, 2013, 2015, 2017, 2019]
HORIZON = 4
SEED = 2026
SIGNAL_STRENGTH = 0.35  # assumed link between signal and outcome; a guess, not a finding

# SOC 2010 -> SOC 2020 bridge. "direct" = same code, "recoded" = one-to-one with
# a new code, "split" = one 2010 group became several, "new" = no 2010 group.
BRIDGE = {
    "2134": ("2136", "recoded"), "2135": ("2139", "new"), "2425": ("2425", "direct"), "3132": ("3132", "direct"),
    "2122": ("2122", "direct"), "2121": ("2121", "direct"), "2123": ("2123", "direct"), "5241": ("5241", "direct"),
    "5314": ("5314", "direct"), "5316": ("5315", "recoded"), "5313": ("5312", "recoded"), "5231": ("5231", "direct"),
    "2232": ("2231", "split"), "2235": ("2231", "split"), "2221": ("2221", "direct"), "2222": ("2222", "direct"),
    "2223": ("2223", "direct"), "2255": ("3213", "recoded"), "2251": ("2213", "recoded"), "2254": ("2217", "recoded"),
    "6135": ("6145", "recoded"), "2313": ("2314", "recoded"), "2314": ("2315", "split"), "2461": ("2442", "recoded"),
    "2225": ("2212", "split"), "2421": ("2421", "direct"), "2412": ("2413", "recoded"), "2451": ("2431", "recoded"),
    "3421": ("3421", "direct"), "2453": ("2433", "recoded"), "2152": ("2142", "recoded"), "5434": ("5434", "direct"),
    "2113": ("2112", "split"), "2240": ("2216", "recoded"), "3312": ("3312", "direct"),
    "2422": ("3534", "recoded"), "2440": ("2424", "recoded"), "3556": ("3545", "recoded"), "3554": ("3543", "recoded"),
    "1122": ("1122", "direct"),
}

# Real-world shocks in an outcome window, so the synthetic series is
# confounded the way the real one will be (COVID hits the 2019 window).
SHOCKS = {2019: {"Hospitality": -9.0, "Health and social care": 4.0, "Digital and technologies": 3.0}}


def build_backtest() -> dict:
    rng = random.Random(SEED)
    se = load("skills_england.json")["occupations"]
    ess = load("ess.json")["editions"]
    years_out = {}
    drift = {soc: rng.uniform(-6, 6) for soc in se}
    for y in YEARS:
        rows = {}
        for soc, row in se.items():
            base_ssv = ess["2024"].get(soc) or ess["2022"].get(soc)
            g = row.get("growth_2035_pct")
            ssv = None if base_ssv is None else max(0.0, round(base_ssv + drift[soc] * (y - 2024) / 13 + rng.gauss(0, 4), 1))
            proj = None if g is None else round(g + rng.gauss(0, 4), 1)
            rows[soc] = {"ssv": ssv, "projection_10y_pct": proj}
        # standardise the demand signal (25:20, the default weights) to draw outcomes
        def z(vals: dict[str, float | None]) -> dict[str, float]:
            present = [v for v in vals.values() if v is not None]
            m = sum(present) / len(present)
            sd = (sum((v - m) ** 2 for v in present) / len(present)) ** 0.5 or 1
            return {k: (0.0 if v is None else (v - m) / sd) for k, v in vals.items()}
        zs = z({k: r["ssv"] for k, r in rows.items()})
        zp = z({k: r["projection_10y_pct"] for k, r in rows.items()})
        for soc, r in rows.items():
            sig = (25 * zp[soc] + 20 * zs[soc]) / 45
            shock = SHOCKS.get(y, {}).get(se[soc]["sector"], 0.0)
            noise = rng.gauss(0, 1) * (1 - SIGNAL_STRENGTH ** 2) ** 0.5
            r["employment_change_pct"] = round(3 + 5 * (SIGNAL_STRENGTH * sig + noise) + shock, 1)
            infl = 9.0 if y == 2019 else 0.0
            r["pay_change_pct"] = round(8 + infl + 2.5 * (SIGNAL_STRENGTH * sig + rng.gauss(0, 1) * 0.9), 1)
            if BRIDGE[soc][1] == "new" and y < 2015:
                r["employment_change_pct"] = None  # no usable 2010-coded series this far back
        years_out[str(y)] = rows
    return {
        "source_id": "backtest",
        "edition": "SYNTHETIC demo series",
        "synthetic": True,
        "_note": "SYNTHETIC DATA. Generated by scripts/build_demo_snapshots.py so the self-grade can be built before the real series are loaded. NOT a track record. Real inputs: ESS 2011-2019 (as published then), Working Futures projections (as published then); real outcomes: LFS employment and ASHE pay, 4 years later.",
        "generator": {"seed": SEED, "signal_strength": SIGNAL_STRENGTH, "horizon_years": HORIZON, "shocks": SHOCKS},
        "horizon_years": HORIZON,
        "bridge": {soc: {"soc2010": c, "type": t} for soc, (c, t) in BRIDGE.items()},
        "years": years_out,
    }


# ------------------------------------------------------------ pay history ----

# Approximate UK CPI annual averages, index 2015 = 100. Written from published annual inflation
# rates (2016 0.7%, 2017 2.7%, 2018 2.5%, 2019 1.8%, 2020 0.9%, 2021 2.6%, 2022 9.1%, 2023 7.3%,
# 2024 2.5%, 2025 about 3.4%). VERIFY against ONS series D7BT before relying on it.
CPI = {2010: 89.4, 2011: 93.4, 2012: 96.0, 2013: 98.5, 2014: 100.0, 2015: 100.0, 2016: 100.7, 2017: 103.4, 2018: 105.9,
       2019: 107.8, 2020: 108.7, 2021: 111.6, 2022: 121.7, 2023: 130.5, 2024: 133.9, 2025: 138.5}
SERIES_YEARS = list(range(2015, 2026))


def build_cpi() -> dict:
    return {
        "source_id": "cpi",
        "edition": "Approximate annual averages (demo snapshot)",
        "base_year": 2015,
        "_note": "Approximate UK Consumer Prices Index annual averages, 2015 = 100, written from the published annual inflation rates. Replace with ONS series D7BT and have a person check every year before relying on it.",
        "index": {str(y): v for y, v in CPI.items()},
    }


def build_pay_series() -> dict:
    """SYNTHETIC history. Anchored to the real shape of ASHE (median, p25, p75), the last two years
    come straight from ashe.json and earlier years are generated backwards with a seeded growth path."""
    rng = random.Random(SEED + 1)
    ashe = load("ashe.json")
    out = {}
    for soc, row in ashe["occupations"].items():
        if row["median"] is None:
            continue  # ONS publishes nothing for this occupation: we do not make a series up
        base_growth = rng.uniform(0.020, 0.040)  # this occupation's usual nominal pay growth per year
        spread_p25 = row["p25"] / row["median"]
        spread_p75 = row["p75"] / row["median"]
        widen = rng.uniform(-0.0025, 0.004)  # spreads drift slowly, some widening, some narrowing
        med = {2025: row["median"], 2024: row["median_prev"]}
        for y in range(2023, 2014, -1):
            g = base_growth
            if y == 2020:
                g = base_growth * 0.3  # pay growth stalled in the pandemic year
            elif y >= 2022:
                g = base_growth + 0.015  # catch-up as prices rose
            g += rng.uniform(-0.006, 0.006)
            med[y] = med[y + 1] / (1 + g)
        rows = {}
        for y in SERIES_YEARS:
            k = (2025 - y)
            lo = max(0.55, spread_p25 - widen * k * 0.6 + rng.uniform(-0.004, 0.004))
            hi = spread_p75 + widen * k * 0.9 + rng.uniform(-0.004, 0.004)
            m = round(med[y] / 100) * 100
            p25 = round(m * lo / 100) * 100
            p75 = round(m * hi / 100) * 100
            if y == 2025:
                m, p25, p75 = row["median"], row["p25"], row["p75"]
            elif y == 2024:
                m = row["median_prev"]
                p25, p75 = round(m * spread_p25 / 100) * 100, round(m * spread_p75 / 100) * 100
            rows[str(y)] = {"p25": min(p25, m - 100), "median": m, "p75": max(p75, m + 100)}
        out[soc] = {"quality": row["quality"], "years": rows}
    return {
        "source_id": "ashe_series",
        "edition": "SYNTHETIC 2015-2025 history (demo snapshot)",
        "synthetic": True,
        "_note": "SYNTHETIC pay history. 2024 and 2025 come from ashe.json (itself demo). Earlier years are generated by scripts/build_demo_snapshots.py with a seeded growth path, to show how the pay dashboard works. NOT real earnings history. Replace with ASHE Table 14 by SOC 2020 (bridged for earlier years) and have a person check it.",
        "generator": {"seed": SEED + 1, "base_growth": "2.0% to 4.0% a year per occupation", "pandemic": "2020 growth x0.3", "catch_up": "+1.5 points from 2022"},
        "occupations": out,
    }


if __name__ == "__main__":
    dump("cpi.json", build_cpi())
    dump("ashe_series.json", build_pay_series())
    dump("regions.json", build_regions())
    dump("nations.json", build_nations())
    dump("backtest.json", build_backtest())
    print("wrote cpi.json, ashe_series.json, regions.json, nations.json, backtest.json")
