"""Read-only tools the guide model can call to fetch Aventier's own data itself.

Every tool runs in the backend from data the app already loads (evidence packs, the occupation
catalogue, the curated path, the committed BlackRock employer file and the Occupations in Demand
table). No tool writes anything or touches the network. Results carry their sources; a tool that
gets bad arguments, an unknown SOC or an unknown name returns `{"error": ...}` instead of raising,
so the model can recover. Each call is recorded as `{name, args, summary}` for the response.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

WEB_DIR = Path(__file__).resolve().parents[1]
DEMAND_FILE = WEB_DIR / "src" / "occupationDemand.ts"
EMPLOYER_FILES = {"blackrock": WEB_DIR / "public" / "employers" / "blackrock.json"}
DEMAND_SOURCE = {
    "name": "Skills England, Occupations in Demand 2025",
    "url": "https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025",
    "coverage": "UK (some indicators GB)",
}
DEMAND_LEVELS = ("Critical", "Elevated", "Not in high demand")
SEARCH_LIMIT = 8
COMPARE_LIMIT = 3
SOC = re.compile(r"^\d{4}$")

_SOC_PARAM = {"type": "string", "pattern": r"^\d{4}$", "description": "4-digit SOC 2020 code, e.g. 2134"}
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "get_role_stats",
        "description": (
            "Sourced statistics for one role: median pay, employee jobs, employment trend, automation exposure "
            "(research estimate), UK demand rating, hedge careers and crisis checks, each with source and caveats."
        ),
        "parameters": {"type": "object", "properties": {"soc": _SOC_PARAM}, "required": ["soc"]},
    },
    {
        "name": "search_jobs",
        "description": (
            "Search the app's UK occupation list by title words, minimum median pay and UK demand rating. "
            "Returns up to 8 roles sorted by demand rating, then median pay."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Words in the job title, e.g. 'engineer'"},
                "min_pay": {"type": "number", "description": "Minimum median full-time pay in GBP a year"},
                "demand": {"type": "string", "enum": list(DEMAND_LEVELS)},
                "limit": {"type": "integer", "minimum": 1, "maximum": SEARCH_LIMIT},
            },
        },
    },
    {
        "name": "compare_roles",
        "description": "Side-by-side pay, jobs, trend, exposure and demand rating for up to 3 roles.",
        "parameters": {
            "type": "object",
            "properties": {"socs": {"type": "array", "items": _SOC_PARAM, "minItems": 1, "maxItems": COMPARE_LIMIT}},
            "required": ["socs"],
        },
    },
    {
        "name": "get_career_path",
        "description": "The app's path into a role: routes, courses, skills to build, a note on grades and a first step.",
        "parameters": {"type": "object", "properties": {"soc": _SOC_PARAM}, "required": ["soc"]},
    },
    {
        "name": "get_employer",
        "description": (
            "Facts from the app's employer file: ways in, career ladder with self-reported UK pay ranges, how pay "
            "works, and sources. Only BlackRock is loaded."
        ),
        "parameters": {"type": "object", "properties": {"name": {"type": "string", "default": "BlackRock"}}},
    },
]
TOOL_NAMES = tuple(spec["name"] for spec in TOOL_SPECS)


@dataclass(frozen=True)
class ToolContext:
    """Accessors into the API's own loaded data (injected by main.py; tests can pass fakes)."""

    pack_for: Callable[[str], dict]  # SOC -> evidence pack; raises for an unknown SOC
    occupations: Callable[[], list[dict]]  # [{soc, title, metrics}] for every catalogue role
    path_for: Callable[[str], dict]  # SOC -> structured career path; raises for an unknown SOC


class ToolError(ValueError):
    """Bad arguments or missing data: returned to the model as {"error": ...}."""


@lru_cache(maxsize=1)
def demand_table() -> dict[str, str]:
    """SOC -> Occupations in Demand rating, read from the table the Jobs page uses ({} when missing)."""
    try:
        text = DEMAND_FILE.read_text(encoding="utf-8")
    except OSError:
        return {}
    return dict(re.findall(r'"(\d{4})":\s*"([^"]+)"', text))


def demand_rating(soc: str) -> dict | None:
    level = demand_table().get(soc)
    return None if level is None else {"rating": level, **DEMAND_SOURCE}


def _soc(value: Any) -> str:
    if not isinstance(value, str) or not SOC.match(value.strip()):
        raise ToolError("soc must be a 4-digit SOC 2020 code")
    return value.strip()


def _pack(ctx: ToolContext, soc: str) -> dict:
    try:
        return ctx.pack_for(soc)
    except Exception as error:  # noqa: BLE001  (HTTP 404 or missing artefact: the model is told plainly)
        raise ToolError(f"no data for SOC {soc}") from error


def _metric(entry: dict) -> dict:
    return {key: entry.get(key) for key in ("label", "display", "source", "as_of", "caveats")}


def _key_metrics(pack: dict) -> dict:
    metrics = pack.get("metrics", {})
    return {
        "soc": pack.get("soc"),
        "title": pack.get("title"),
        **{key: metrics[key].get("display") for key in ("pay", "jobs", "trend", "exposure") if key in metrics},
        "demand": demand_rating(str(pack.get("soc"))),
    }


def get_role_stats(ctx: ToolContext, args: dict) -> tuple[dict, str]:
    soc = _soc(args.get("soc"))
    pack = _pack(ctx, soc)
    metrics = {key: _metric(entry) for key, entry in pack.get("metrics", {}).items() if entry.get("value") is not None}
    hedges = [
        {k: h.get(k) for k in ("soc", "title", "why", "lower_exposure")}
        | {"pay": h["pay"]["display"], "trend": h["trend"]["display"]}
        for h in pack.get("hedges", [])
    ]
    crises = [
        {"name": c.get("name"), "period": c.get("period"), "result": (c.get("result") or {}).get("display"),
         "excluded_from_recommendations": c.get("excluded_from_recommendations")}
        for c in pack.get("crises", [])
    ]
    demand = demand_rating(soc)
    result = {
        "soc": soc,
        "title": pack.get("title"),
        "metrics": metrics,
        "demand": demand,
        "hedges": hedges,
        "crisis_checks": crises,
        "note": "Observed history, not a forecast. Exposure is a research estimate, not job loss.",
        "sources": [{k: s.get(k) for k in ("name", "url")} for s in pack.get("sources", [])],
    }
    parts = [key for key in ("pay", "jobs", "trend", "exposure") if key in metrics]
    if demand:
        parts.append("demand")
    parts.append(f"{len(hedges)} hedges")
    return result, f"get_role_stats({soc}): " + ", ".join(parts)


_RANK = {level: rank for rank, level in enumerate(DEMAND_LEVELS)}


def search_jobs(ctx: ToolContext, args: dict) -> tuple[dict, str]:
    query = args.get("query") or ""
    if not isinstance(query, str) or len(query) > 80:
        raise ToolError("query must be a short string")
    min_pay = args.get("min_pay")
    if min_pay is not None and (isinstance(min_pay, bool) or not isinstance(min_pay, (int, float)) or min_pay < 0):
        raise ToolError("min_pay must be a non-negative number")
    demand = args.get("demand")
    if demand is not None:
        matched = [level for level in DEMAND_LEVELS if isinstance(demand, str) and level.lower() == demand.strip().lower()]
        if not matched:
            raise ToolError("demand must be one of: " + ", ".join(DEMAND_LEVELS))
        demand = matched[0]
    limit = args.get("limit", 5)
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ToolError("limit must be an integer from 1 to 8")
    limit = max(1, min(limit, SEARCH_LIMIT))
    words = query.lower().split()
    rows = []
    for occupation in ctx.occupations():
        soc, title = occupation["soc"], occupation["title"]
        if words and not all(word in title.lower() for word in words):
            continue
        pay = occupation.get("metrics", {}).get("pay_median", {})
        trend = occupation.get("metrics", {}).get("demand_trend", {})
        if min_pay is not None and (pay.get("value") is None or pay["value"] < min_pay):
            continue
        level = demand_table().get(soc)
        if demand is not None and level != demand:
            continue
        rows.append(
            {
                "soc": soc,
                "title": title,
                "median_pay": None if pay.get("value") is None else f"£{pay['value']:,.0f}",
                "pay_as_of": pay.get("as_of"),
                "trend": None if trend.get("value") is None else f"{100 * trend['value']:+.2f}% a year",
                "trend_as_of": trend.get("as_of"),
                "demand": level,
                "_pay": pay.get("value"),
            }
        )
    rows.sort(key=lambda r: (_RANK.get(r["demand"], len(DEMAND_LEVELS)), -(r["_pay"] or 0), r["soc"]))
    results = [{k: v for k, v in row.items() if k != "_pay"} for row in rows[:limit]]
    result = {
        "results": results,
        "matched": len(rows),
        "sources": [{"name": "ONS ASHE (pay, trend)"}, DEMAND_SOURCE],
        "note": "Pay is the median for full-time employees, not starting pay. Trend is history, not a forecast.",
    }
    shown = ", ".join(f"{k}={v}" for k, v in (("query", query), ("min_pay", min_pay), ("demand", demand)) if v)
    return result, f"search_jobs({shown}): {len(results)} of {len(rows)} roles"


def compare_roles(ctx: ToolContext, args: dict) -> tuple[dict, str]:
    socs = args.get("socs")
    if not isinstance(socs, list) or not 1 <= len(socs) <= COMPARE_LIMIT:
        raise ToolError(f"socs must be a list of 1 to {COMPARE_LIMIT} SOC codes")
    socs = list(dict.fromkeys(_soc(soc) for soc in socs))
    roles = [_key_metrics(_pack(ctx, soc)) for soc in socs]
    result = {"roles": roles, "note": "Observed history, not a forecast; exposure is a research estimate, not job loss."}
    return result, f"compare_roles({', '.join(socs)}): pay, jobs, trend, exposure, demand"


def get_career_path(ctx: ToolContext, args: dict) -> tuple[dict, str]:
    soc = _soc(args.get("soc"))
    try:
        path = ctx.path_for(soc)
    except Exception as error:  # noqa: BLE001
        raise ToolError(f"no path for SOC {soc}") from error
    summary = f"get_career_path({soc}): {len(path.get('routes', []))} routes, {len(path.get('courses', []))} courses"
    return {"soc": soc, **path}, summary


@lru_cache(maxsize=4)
def _employer_file(key: str) -> dict:
    return json.loads(EMPLOYER_FILES[key].read_text(encoding="utf-8"))


def get_employer(ctx: ToolContext, args: dict) -> tuple[dict, str]:
    name = args.get("name") or "BlackRock"
    key = re.sub(r"[^a-z]", "", name.lower()) if isinstance(name, str) else ""
    if key not in EMPLOYER_FILES:
        raise ToolError("only BlackRock is loaded; no other employer file exists")
    try:
        data = _employer_file(key)
    except (OSError, ValueError) as error:
        raise ToolError("the employer file could not be read") from error
    official = data.get("official", {})
    result = {
        "employer": data.get("employer"),
        "as_of": data.get("as_of"),
        "ways_in": official.get("ways_in", []),
        "entry_routes": data.get("entry_routes"),
        "career_ladder_uk": data.get("career_ladder_uk"),
        "pay_works": official.get("pay_works", []),
        "median_pay": official.get("median_pay"),
        "sources": official.get("sources", {}),
        "note": "Only what the app's employer file says; self-reported pay ranges are not offers.",
    }
    return result, f"get_employer({data.get('employer')}): ways in, ladder, pay structure"


TOOLS: dict[str, Callable[[ToolContext, dict], tuple[dict, str]]] = {
    "get_role_stats": get_role_stats,
    "search_jobs": search_jobs,
    "compare_roles": compare_roles,
    "get_career_path": get_career_path,
    "get_employer": get_employer,
}


def run_tool(ctx: ToolContext, name: Any, args: Any) -> tuple[dict, str]:
    """(result, one-line summary). Never raises: unknown names and bad arguments come back as errors."""
    tool = TOOLS.get(name) if isinstance(name, str) else None
    if tool is None:
        return {"error": f"unknown tool; available: {', '.join(TOOL_NAMES)}"}, f"{name}: unknown tool"
    if not isinstance(args, dict):
        return {"error": "arguments must be a JSON object"}, f"{name}: bad arguments"
    try:
        return tool(ctx, args)
    except ToolError as error:
        return {"error": str(error)}, f"{name}: error, {error}"
    except Exception as error:  # noqa: BLE001  (a tool bug must not break the guide)
        return {"error": "the tool failed"}, f"{name}: failed ({type(error).__name__})"


def parse_args(raw: Any) -> Any:
    """Tool arguments as sent by the model: a JSON string (OpenAI) or an object (Anthropic); None when invalid."""
    if isinstance(raw, dict):
        return raw
    if raw in (None, ""):
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def openai_tools() -> list[dict]:
    return [{"type": "function", "function": spec} for spec in TOOL_SPECS]


def anthropic_tools() -> list[dict]:
    return [{"name": s["name"], "description": s["description"], "input_schema": s["parameters"]} for s in TOOL_SPECS]
