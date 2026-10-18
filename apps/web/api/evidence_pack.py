"""One compact, display-ready evidence pack per role, assembled from the loaded artefacts.

Pure assembly: no network, no new numbers. Every figure keeps its source, year, status and the
caveat sentences the app shows (FLAG_TEXT / MUST_MENTION plus the provisional note). History is
history, not a forecast. `allowed_numbers` lists every number in the pack, canonicalised with the
LLM writer's rules, so a model's reply can be checked against it.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from pathfinder_ml import FLAG_TEXT, ML, MUST_MENTION

from avenir_adapters.llm.writer import _canon, numbers_in

from .evidence_metadata import demand_comparison, evidence_metadata

HISTORY_YEARS = (2011, 2015, 2019, 2022)
HEDGE_COUNT = 3
FIT_TAG_COUNT = 3
AUDIENCE = "a 17-year-old in the UK choosing a career"
SOURCE_FIELDS = ("name", "publisher", "url", "licence", "coverage")

# Crisis checks in crises.json map to resilience metrics on the occupation (same rule as product_data).
_CRISIS_METRIC = {"gfc_2008": "resilience_2008"}


def metric_caveats(metric: dict) -> list[str]:
    """The caveat sentences the app shows for a metric: supplied status, provisional note and FLAG_TEXT."""
    notes = []
    if metric.get("status") == "preliminary":
        notes.append("The supplied estimate is preliminary.")
    for flag in metric.get("flags", []):
        if flag == "provisional":
            years = re.findall(r"\b20\d{2}\b", metric.get("as_of", ""))
            label = f"The {years[-1]} figure" if years else "This figure"
            notes.append(f"{label} is an ONS provisional estimate and may be revised.")
        elif flag in MUST_MENTION or flag in ("multi_isco", "sources_disagree", "category_level"):
            if flag in FLAG_TEXT:
                notes.append(FLAG_TEXT[flag])
            if flag == "category_level" and metric.get("extra", {}).get("adverts_category"):
                notes.append("The broad job-advert category is " + metric["extra"]["adverts_category"] + ".")
    return notes


def _gbp(value: float | None) -> str | None:
    return None if value is None else f"£{value:,.0f}"


def _pct(value: float | None, places: int = 2) -> str | None:
    return None if value is None else f"{100 * value:+.{places}f}%"


def _entry(label: str, metric: dict, display: str | None) -> dict:
    return {
        "label": label,
        "value": metric.get("value"),
        "display": display,
        "unit": metric.get("unit"),
        "source": metric.get("source"),
        "as_of": metric.get("as_of"),
        "status": metric.get("status"),
        "flags": list(metric.get("flags", [])),
        "caveats": metric_caveats(metric),
    }


def _metrics(metrics: dict) -> dict:
    pay = metrics.get("pay_median", {})
    pay_display = None
    if pay.get("value") is not None:
        pay_display = f"{_gbp(pay['value'])} a year, median for full-time employees ({pay.get('as_of')})"
        if pay.get("low") is not None and pay.get("high") is not None:
            pay_display += f"; the middle half earn {_gbp(pay['low'])}–{_gbp(pay['high'])}"
    jobs = metrics.get("jobs", {})
    jobs_display = None
    if jobs.get("value") is not None:
        jobs_display = f"{jobs['value']:,.0f} thousand full-time employee jobs ({jobs.get('as_of')})"
    trend = metrics.get("demand_trend", {})
    trend_display = None
    if trend.get("value") is not None:
        trend_display = f"{_pct(trend['value'])} a year{demand_comparison(trend)} over {trend.get('as_of')}"
        typical = trend.get("extra", {}).get("typical_occupation_trend")
        if typical is not None:
            trend_display += f" (typical occupation {_pct(typical)} a year)"
        trend_display += "; this is history, not a forecast"
    exposure = metrics.get("exposure", {})
    exposure_display = None
    if exposure.get("value") is not None:
        exposure_display = f"{exposure['value']:.4f} on a 0–1 scale (research estimate, not job loss)"
        if exposure.get("low") is not None and exposure.get("high") is not None:
            exposure_display += f"; research range {exposure['low']:.4f}–{exposure['high']:.4f}"
    return {
        "pay": _entry("Median pay, full-time employees", pay, pay_display),
        "jobs": _entry("Employee jobs", jobs, jobs_display),
        "trend": _entry("Employment trend 2022-2025 vs the typical occupation", trend, trend_display),
        "exposure": _entry("Automation exposure (research estimate)", exposure, exposure_display),
    }


def _history(points: list[dict], price_label: str) -> dict:
    by_year = {point["year"]: point for point in points if point.get("year") is not None}
    years = [year for year in HISTORY_YEARS if year in by_year]
    latest = max(by_year) if by_year else None
    if latest is not None and latest not in years:
        years.append(latest)
    chosen = [by_year[year] for year in years]
    flags = {flag for point in chosen for flag in point.get("flags", [])}
    caveats = [FLAG_TEXT["recoded_2021"]] + [FLAG_TEXT[f] for f in sorted(flags) if f in MUST_MENTION and f != "recoded_2021"]
    return {
        "price_base": f"{price_label}, tax-year CPIH",
        "points": [
            {
                "year": point["year"],
                "pay_median_nominal": point.get("pay_median"),
                "pay_median_real": point.get("pay_median_real"),
                "jobs_k": point.get("jobs_k"),
                "flags": list(point.get("flags", [])),
            }
            for point in chosen
        ],
        "caveats": caveats,
        "note": "Observed past values; they do not predict future pay or jobs.",
    }


def _hedges(evidence: ML, hedges: list[dict]) -> list[dict]:
    out = []
    for hedge in hedges[:HEDGE_COUNT]:
        occupation = evidence.occupation(hedge["soc2020"])
        metrics = occupation["metrics"] if occupation else {}
        pay = metrics.get("pay_median", {})
        trend = metrics.get("demand_trend", {})
        out.append(
            {
                "soc": hedge["soc2020"],
                "title": (occupation or {}).get("short_title") or hedge.get("title"),
                "similarity": hedge.get("similarity"),
                "evidence": hedge.get("evidence"),
                "status": hedge.get("status"),
                "why": hedge.get("why"),
                "lower_exposure": hedge.get("lower_exposure"),
                "exposure_delta": hedge.get("exposure_delta"),
                "pay": {
                    "value": pay.get("value"),
                    "display": _gbp(pay.get("value")),
                    "as_of": pay.get("as_of"),
                    "source": pay.get("source"),
                },
                "trend": {
                    "value": trend.get("value"),
                    "display": _pct(trend.get("value")),
                    "as_of": trend.get("as_of"),
                    "source": trend.get("source"),
                },
            }
        )
    return out


def _backtest(evidence: ML, soc: str) -> dict | None:
    try:
        artefact = evidence._load("backtest")
    except (FileNotFoundError, ValueError):
        return None
    windows = []
    for window in artefact.get("windows", []):
        mine = next((o for o in window.get("occupations", []) if str(o.get("soc2020")) == soc), None)
        if mine is None:
            continue
        group = next((g for g in window.get("groups", []) if g.get("key") == mine.get("group_then")), {})
        windows.append(
            {
                "base_year": window.get("base_year"),
                "outcome_year": window.get("outcome_year"),
                "rule_group_then": mine.get("group_then"),
                "group_real_pay_growth_median": (group.get("real_pay_growth") or {}).get("median"),
                "group_jobs_growth_median": (group.get("jobs_growth") or {}).get("median"),
                "this_role_real_pay_growth": mine.get("real_pay_growth"),
                "this_role_jobs_growth": mine.get("jobs_growth"),
                "jobs_comparable": window.get("jobs_comparable"),
            }
        )
    if not windows:
        return None
    return {
        "status": artefact.get("status"),
        "rules": artefact.get("method"),
        "windows": windows,
        "caveats": list(artefact.get("caveats", [])),
    }


def _crises(evidence: ML, metrics: dict) -> list[dict]:
    out = []
    for crisis in evidence.crises():
        key = crisis.get("key", "")
        placebo = crisis.get("placebo") or {}
        passed = placebo.get("passes")
        excluded = passed is False or crisis.get("show_on_card") is False
        metric = metrics.get(_CRISIS_METRIC.get(key, f"resilience_{key}"))
        result = None
        if metric and metric.get("value") is not None:
            result = {
                "value": metric["value"],
                "display": f"{_pct(metric['value'], 1)} relative to the typical occupation ({metric.get('as_of')})",
                "source": metric.get("source"),
                "status": metric.get("status"),
                "caveats": metric_caveats(metric),
            }
        out.append(
            {
                "key": key,
                "name": crisis.get("label"),
                "period": crisis.get("window"),
                "placebo_passed": passed,
                "excluded_from_recommendations": excluded,
                "result": result,
            }
        )
    return out


def _fit_tags(evidence: ML, soc: str) -> list[dict] | None:
    affinity = evidence.affinity()
    labels = {tag["id"]: tag.get("label", tag["id"]) for tag in evidence.tags()}
    scores = [(tag, table[soc]) for tag, table in affinity.items() if soc in table]
    if not scores:
        return None
    scores.sort(key=lambda item: (-item[1], item[0]))
    return [{"tag": tag, "label": labels.get(tag, tag), "affinity": score} for tag, score in scores[:FIT_TAG_COUNT]]


def _sources(evidence: ML, keys: list[str]) -> list[dict]:
    registry = evidence.sources()
    return [
        {"id": key, **{field: registry[key].get(field) for field in SOURCE_FIELDS}}
        for key in dict.fromkeys(keys)
        if key in registry
    ]


def _walk(obj: Any):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _walk(value)
    else:
        yield obj


def allowed_numbers(pack: dict) -> set[str]:
    """Every number in the pack as a model may write it: numbers inside strings, plus numeric values
    with 0 to 4 decimal places and, for fractions, as percentages with 0 to 2 places."""
    allowed: set[str] = set()
    for value in _walk(pack):
        if isinstance(value, str):
            allowed |= numbers_in(value)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                allowed.add(_canon(str(Decimal(str(value)))))
                for places in (0, 1, 2, 4):
                    allowed.add(_canon(f"{value:.{places}f}"))
                if abs(value) <= 1:
                    for places in (0, 1, 2):
                        allowed.add(_canon(f"{value * 100:.{places}f}"))
            except (InvalidOperation, ValueError):
                continue
    return allowed


SHORT_SOURCE = {
    "ons_ashe_t14": "ONS ASHE",
    "ons_cpih": "ONS CPIH",
    "ilo_wp140": "ILO WP140",
    "dfe_ai_uk_2023": "DfE 2023",
    "ons_online_job_adverts": "ONS job adverts",
}


def based_on_lines(pack: dict) -> list[str]:
    """Short stat lines naming the figure, its source and year, for the guide's `based_on` field."""
    lines = []
    for key, entry in pack.get("metrics", {}).items():
        if entry.get("value") is None:
            continue
        short = SHORT_SOURCE.get(entry.get("source"), entry.get("source") or "unknown source")
        status = ", provisional" if "provisional" in entry.get("flags", []) else ""
        if key == "pay":
            lines.append(f"Median pay {_gbp(entry['value'])} ({short} {entry.get('as_of')}{status})")
        elif key == "jobs":
            lines.append(f"Employee jobs {entry['value']:,.0f} thousand ({short} {entry.get('as_of')}{status})")
        elif key == "trend":
            lines.append(f"Employment trend {_pct(entry['value'])} a year vs typical ({short} {entry.get('as_of')}{status})")
        elif key == "exposure":
            lines.append(f"Automation exposure {entry['value']:.4f} ({short} {entry.get('as_of')})")
    return lines


ESCO_SKILL_COUNT = 8


def esco_skills(evidence: ML, soc: str, count: int = ESCO_SKILL_COUNT) -> list[str]:
    """The role's first ESCO skills from `career_texts`, or [] when the file or the role is missing."""
    try:
        entry = evidence._load("career_texts").get(soc)
    except (FileNotFoundError, ValueError):
        return []
    skills = entry.get("skills", []) if isinstance(entry, dict) else []
    return [str(skill) for skill in skills[:count]]


def build_evidence_pack(evidence: ML, career: dict) -> dict:
    """The pack for one career payload (the `/api/careers/{soc}` object). Pure; no I/O beyond the loaded artefacts."""
    soc = career["soc"]
    metrics = career["metrics"]
    price_label = career.get("evidence_metadata", {}).get("price_label") or evidence_metadata(evidence)["price_label"]
    pack_metrics = _metrics(metrics)
    source_keys = [entry["source"] for entry in pack_metrics.values() if entry.get("source")] + ["ons_cpih"]
    source_keys += [crisis["result"]["source"] for crisis in _crises(evidence, metrics) if crisis["result"]]
    pack = {
        "soc": soc,
        "title": career["title"],
        "summary": career.get("summary"),
        "audience": AUDIENCE,
        "metrics": pack_metrics,
        "history": _history(career.get("history") or evidence.history(soc), price_label),
        "hedges": _hedges(evidence, career.get("hedges") or evidence.hedges(soc, k=5)),
        "backtest": _backtest(evidence, soc),
        "backtest_note": None,
        "crises": _crises(evidence, metrics),
        "fit_tags": _fit_tags(evidence, soc),
        "demand": career.get("demand"),
        "starting_pay": career.get("starting_pay"),
        "sources": _sources(evidence, source_keys),
    }
    if pack["backtest"] is None:
        pack["backtest_note"] = "The historical rule checks do not score this occupation (no data at both ends of a window)."
    if pack["demand"] is None:
        pack["demand_note"] = "No Occupations in Demand assessment is loaded for this role."
    if pack["starting_pay"] is None:
        pack["starting_pay_note"] = "No starting-pay figure is loaded; the median is not starting pay."
    pack["skills"] = esco_skills(evidence, soc)
    pack["based_on"] = based_on_lines(pack)
    pack["allowed_numbers"] = sorted(allowed_numbers(pack))
    return pack
