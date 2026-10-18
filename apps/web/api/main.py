"""Local app API joining Arsenii's evidence to Max's original pathway planner.

Run from apps/web: python -m uvicorn api.main:app --port 8000
All paths resolve from this file. No keys or network calls are needed.
"""

from __future__ import annotations

import copy
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi import Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[3]
for module_dir in (REPO_ROOT / "packages/ml", REPO_ROOT / "prototypes/pathfinder-game/backend"):
    sys.path.insert(0, str(module_dir))

from app.data import get_store  # noqa: E402
from app.path import build_plan  # noqa: E402
from pathfinder_ml import FLAG_TEXT, ML, MUST_MENTION  # noqa: E402

from .catalogue import detail as catalogue_detail  # noqa: E402
from .catalogue import summaries as catalogue_summaries  # noqa: E402
from .discovery import DiscoveryRequest, discover  # noqa: E402
from .evidence_metadata import demand_comparison, evidence_metadata  # noqa: E402
from .ranking import rank_careers  # noqa: E402

app = FastAPI(title="Avenir app API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (4175, 5173)],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Text/pathway bridges only. Numeric data ALWAYS retains the requested ML SOC.
# These map ML careers absent from Max's earlier 40-career prototype to a
# related teaching example, with explicit disclosure in the returned path.
TEXT_BRIDGES = {
    "3544": "2425",
    "2133": "2134",
    "2141": "3421",
    "2142": "3421",
    "2452": "2451",
    "3120": "2451",
    "3113": "2122",
    "2454": "2453",
    "2433": "2425",
}

# Display categories describe the requested ML occupation. They are independent
# of the related occupation occasionally used for a curated pathway example.
DISPLAY_SECTORS = {
    "2134": "Software and technology",
    "3544": "Data and analytics",
    "2133": "Business and technology",
    "2135": "Cyber security",
    "2141": "Digital design",
    "2142": "Design and creative",
    "2451": "Architecture and built environment",
    "2452": "Planning and built environment",
    "3120": "Technical design and built environment",
    "2121": "Civil engineering",
    "2123": "Electrical engineering",
    "3113": "Engineering and manufacturing",
    "2453": "Surveying and construction",
    "2454": "Property and surveying",
    "2433": "Finance and quantitative sciences",
    "2422": "Finance and investment",
    "2421": "Accounting and finance",
    "2254": "Healthcare and diagnostics",
    "5241": "Skilled trades and energy",
    "5315": "Skilled trades and energy",
    "2313": "Education",
}


class Weights(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    pay: float = Field(default=1, ge=0, le=100)
    interest: float = Field(default=1, ge=0, le=100)
    need: float = Field(default=1, ge=0, le=100)


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tags: list[str] = Field(default_factory=list, max_length=32)
    weights: Weights = Field(default_factory=Weights)


class GuideTurn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class GuideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    soc: str = Field(pattern=r"^\d{4}$")
    message: str = Field(min_length=1, max_length=2000)
    history: list[GuideTurn] = Field(default_factory=list, max_length=30)


@lru_cache(maxsize=1)
def ml() -> ML:
    return ML()


def _text_soc(soc: str) -> str:
    return soc if soc in get_store().occupations else TEXT_BRIDGES.get(soc, soc)


@lru_cache(maxsize=1)
def _careers() -> list[dict]:
    store = get_store()
    output = []
    occupations = ml().occupations(demo_only=True)
    metadata = evidence_metadata(ml())
    plumber = ml().occupation("5315")
    if plumber is not None and all(occupation["soc2020"] != "5315" for occupation in occupations):
        occupations.append(plumber)
    for occupation in occupations:
        soc = occupation["soc2020"]
        text_soc = _text_soc(soc)
        text = store.occupations.get(text_soc)
        family = store.family_of.get(text_soc, "explore")
        fam = store.pathways["families"].get(family, {})
        skills = [item["skill"] for item in fam.get("hard", [])]
        title = occupation.get("short_title") or occupation["title"]
        summary = (
            text.summary
            if text and text_soc == soc
            else (
                f"Explore {title.lower()} through practical projects, relevant study "
                "and conversations with people doing the work."
            )
        )
        if soc == "5315":
            title = "Plumber"
            summary = "Install and repair water and heating systems in homes and commercial buildings."
            skills = ["Practical problem solving", "Working with tools", "Attention to detail", "Customer communication"]
        output.append(
            {
                "soc": soc,
                "evidence_metadata": metadata,
                "title": title,
                "summary": summary,
                "sector": DISPLAY_SECTORS.get(soc, "Career exploration"),
                "family": family,
                "skills": skills or (text.skills_build if text else []),
                "metrics": occupation["metrics"],
                "history": ml().history(soc),
                "hedges": ml().hedges(soc, k=5),
            }
        )
    return output


def _match_careers() -> list[dict]:
    """Matching stays within the 20 careers covered by the supplied affinity model."""
    demo_socs = {occupation["soc2020"] for occupation in ml().occupations(demo_only=True)}
    return [career for career in _careers() if career["soc"] in demo_socs]


def _career(soc: str) -> dict:
    found = catalogue_detail(ml(), soc, _careers())
    if found is None:
        raise HTTPException(404, "Career not found")
    return found


@app.get("/api/catalogue")
def catalogue() -> list[dict]:
    return catalogue_summaries(ml(), _careers())


@app.get("/api/careers/{soc}")
def career_detail(soc: str = ApiPath(pattern=r"^\d{4}$")) -> dict:
    return _career(soc)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "careers": len(_careers()), "ml_mode": ml().status()["mode"], "guide_mode": "prepared_demo"}


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    status = ml().status()
    fit = ml()._load("fit")
    return {
        "careers": _careers(),
        "evidence_metadata": evidence_metadata(ml()),
        "tags": ml().tags(),
        "sources": ml().sources(),
        "backtest": ml()._load("backtest"),
        "crises": ml().crises(),
        "data_status": {
            "mode": status["mode"],
            "artefacts": {name: details["status"] for name, details in status["artefacts"].items()},
            "origins": {name: details.get("origin") for name, details in status["artefacts"].items()},
            "fit": fit["status"],
            "fit_method": fit.get("method"),
            "fit_evaluation": fit.get("evaluation"),
            "hedges": ml()._load("hedges")["status"],
            "pathways": "curated_demo",
            "guide": "prepared_demo",
            "note": (
                "Career evidence and matching use Arsenii's committed dataset and supplied affinities. "
                "The matching method and evaluation limits are supplied alongside its status. "
                "Pathways are Max's curated examples."
            ),
        },
    }


@app.post("/api/matches")
def matches(request: MatchRequest) -> dict:
    fit = ml()._load("fit")
    try:
        results = rank_careers(
            _match_careers(), request.tags, request.weights.model_dump(), fit["affinity"], fit_status=fit["status"]
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {
        "results": results,
        "method": (
            "Weighted mean of pay percentile, supplied interest affinity and observed demand percentile. "
            "Missing evidence is excluded; zero weights use equal importance. "
            "Demand is historical, not an LLM forecast."
        ),
        "fit_status": fit["status"],
    }


@app.post("/api/discovery")
def discovery(request: DiscoveryRequest) -> dict:
    try:
        matches = ml().match_tags(request.answers.positive_activity_text(), top_k=16)
        return discover(request, _match_careers(), matches, ml()._load("fit"))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@app.get("/api/path/{soc}")
def path(soc: str = ApiPath(pattern=r"^\d{4}$"), nation: str = "Scotland") -> dict:
    career = _career(soc)
    if not career["pathway_available"]:
        raise HTTPException(404, "A pathway example is not available for this career yet")
    nation_names = {n.lower().replace("_", " "): n for n in ("Scotland", "England", "Wales", "Northern Ireland")}
    nation = nation_names.get(nation.lower().replace("_", " "), "Scotland")
    text_soc = _text_soc(soc)
    plan = build_plan(get_store(), text_soc, nation)
    if plan is None:
        raise HTTPException(404, "A pathway example is not available for this career yet")
    data = copy.deepcopy(plan.model_dump())
    data.update(soc=soc, title=career["title"], summary=career["summary"], pathway_status="curated_demo")
    # Max's original prototype earnings are illustrative and must never replace
    # Arsenii's sourced evidence. The API does not serve them as career statistics.
    for degree in data["degrees"]:
        degree["median_earnings_15m"] = None
    if text_soc != soc:
        data["related_pathway_soc"] = text_soc
        data["demo_note"] = (
            f"This is a related {get_store().occupations[text_soc].title.lower()} pathway example "
            f"adapted for {career['title'].lower()}; check requirements for the exact career. " + data["demo_note"]
        )
    return data


def _source_refs(keys: list[str]) -> list[dict]:
    registry = ml().sources()
    registry["ncs_plumber"] = {
        "name": "National Careers Service: plumber",
        "publisher": "Department for Education",
        "url": "https://nationalcareers.service.gov.uk/job-profiles/plumber",
        "coverage": "England careers guidance",
        "licence": "Open Government Licence v3.0",
    }
    return [{"id": key, **registry[key]} for key in keys if key in registry]


def _evidence_note(metric: dict) -> str:
    """Keep the supplied status and applicable data caveats visible in replies."""
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
    return " " + " ".join(notes) if notes else ""


def _guide_reply(career: dict, message: str, history: list[GuideTurn]) -> tuple[str, list[str]]:
    lower = message.lower()
    # A prepared guide does not interpret instructions or generate arbitrary content.
    if re.search(
        r"ignore (all |previous |your )|system prompt|write .*(poem|story|code)|politic|recipe|weather|football|malware", lower
    ):
        return (
            "I can help explore this career: the work, pay, skills, study routes and automation evidence. "
            "Try asking what to learn first or how salaries compare after inflation.",
            [],
        )
    if re.fullmatch(r"(and |what about )?(that|it|more|why)[?.! ]*", lower):
        previous = next((turn.content for turn in reversed(history) if turn.role == "user"), "")
        lower += " " + previous.lower()
    metrics = career["metrics"]
    if re.search(r"\b(pay|salary|salaries|earn\w*|inflation|money|income)\b", lower):
        pay = metrics.get("pay_median", {})
        value = pay.get("value")
        if value is None:
            return (
                f"The supplied dataset has no reliable median salary for {career['title'].lower()}. "
                "Missing evidence stays missing. Compare the work and routes while checking ONS for updated figures.",
                ["ons_ashe_t14"],
            )
        text = f"The published median for {career['title'].lower()} is £{value:,.0f} a year ({pay.get('as_of', 'latest year')})."
        if pay.get("low") is not None and pay.get("high") is not None:
            text += (
                f" The middle half of full-time employees earn £{pay['low']:,.0f}–£{pay['high']:,.0f}; "
                "this is not a starting-salary promise."
            )
        text += (
            " Use the inflation-adjusted chart to compare purchasing power in "
            + career["evidence_metadata"]["price_label"] + "."
        )
        text += _evidence_note(pay)
        return text, ["ons_ashe_t14", "ons_cpih"]
    if any(word in lower for word in (" ai", "ai ", "automation", "robot", "replace", "exposure")) or lower == "ai":
        exposure = metrics.get("exposure", {})
        if exposure.get("value") is None:
            return (
                "Automation exposure is not available for this career in the supplied dataset. "
                "It would be misleading to predict job loss. Build transferable skills "
                "and revisit the evidence as it develops.",
                ["ilo_wp140"],
            )
        text = (
            f"The ILO research estimate of task exposure is {exposure['value']:.4f} on a 0–1 scale. "
            "Exposure is not a forecast of job losses: it describes tasks that generative AI could affect."
        )
        if exposure.get("low") is not None and exposure.get("high") is not None:
            text += f" The supplied range is {exposure['low']:.4f}–{exposure['high']:.4f}."
        text += _evidence_note(exposure)
        text += " Strengthen judgement, communication and the ability to check AI output alongside your practical skills."
        return text, ["ilo_wp140"]
    if any(word in lower for word in ("need", "demand", "future", "growth", "opportunit", "jobs", "forecast")):
        demand = metrics.get("demand_trend", {})
        if demand.get("value") is None:
            return (
                "The supplied dataset has no reliable employment trend for this career. "
                "The app cannot honestly estimate how needed it will be from missing evidence.",
                ["ons_ashe_t14"],
            )
        return (
            f"The observed employee-job trend{demand_comparison(demand)} was {100 * demand['value']:+.2f}% per year "
            f"over {demand.get('as_of') or 'the supplied period'}. This is a historical signal, "
            "not a prediction or a promise of a vacancy. Compare it with your interest "
            "in the day-to-day work and build skills that transfer between roles. "
            + demand.get("note", "") + _evidence_note(demand),
            ["ons_ashe_t14"],
        )
    if career["soc"] == "5315":
        return (
            career["summary"] + " Detailed skills and study routes for this profile have not been added yet. "
            "The National Careers Service describes college, apprenticeship and on-the-job routes. "
            "Check its plumber profile for the route and entry requirements that fit your situation.",
            ["ncs_plumber"],
        )
    if not career["pathway_available"]:
        return (
            career["summary"] + " Personalised matching currently covers 20 careers. "
            "This occupation is available for evidence browsing; check an official careers service "
            "for occupation-specific training and entry requirements.",
            [],
        )
    plan = path(career["soc"])
    if any(word in lower for word in ("skill", "learn", "good at", "practice", "project")):
        skills = plan.get("hard_skills", [])[:3]
        text = "Build evidence of skill through small projects: " + "; ".join(
            f"{item['skill']}: {item['how']}" for item in skills
        )
        text += " " + " ".join(item["how"] for item in plan.get("soft_skills", [])[:1])
        return text, []
    if any(
        word in lower
        for word in (
            "university",
            "universities",
            "degree",
            "study",
            "route",
            "start",
            "path",
            "apprentice",
            "course",
            "event",
            "societ",
        )
    ):
        text = plan["first_step"]
        # A related pathway is an exploration example, not evidence that its
        # occupation-specific entry requirements apply to the requested career.
        if not plan.get("related_pathway_soc"):
            text += " " + plan["degree_role"]["note"]
        if career["soc"] == "2433":
            text += (
                " This group covers actuaries, economists and statisticians. "
                "Their study routes and entry requirements differ; check the exact career you want to explore."
            )
        subjects = [degree["subject"] for degree in plan["degrees"]]
        if subjects:
            text += " Degree subjects to compare: " + ", ".join(subjects[:3]) + "."
        text += " " + plan["demo_note"]
        return text, []
    if any(
        word in lower for word in ("career", "work", "role", "day", "tell", "hello", "hi", "help", "fit", "interest", "enjoy")
    ):
        return career["summary"] + " " + plan[
            "first_step"
        ] + " Ask me about pay, skills, study routes, demand or automation evidence.", []
    return (
        "This prepared guide focuses on your career choice. Ask about the work, pay, skills, "
        "study routes, demand or automation evidence.",
        [],
    )


@app.post("/api/guide")
def guide(request: GuideRequest) -> dict:
    text, keys = _guide_reply(_career(request.soc), request.message, request.history)
    return {
        "text": text,
        "mode": "prepared_demo",
        "ai_written": False,
        "sources": _source_refs(keys),
        "note": "Prepared demo guide using the supplied data and curated pathways; no live language model is connected.",
    }
