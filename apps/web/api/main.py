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
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
for module_dir in (REPO_ROOT / "packages/ml", REPO_ROOT / "prototypes/pathfinder-game/backend"):
    sys.path.insert(0, str(module_dir))

from app.data import get_store  # noqa: E402
from app.path import build_plan  # noqa: E402
from pathfinder_ml import ML  # noqa: E402

from . import guide_cache, rate_limit  # noqa: E402
from .catalogue import detail as catalogue_detail  # noqa: E402
from .catalogue import summaries as catalogue_summaries  # noqa: E402
from .discovery import DiscoveryRequest, discover  # noqa: E402
from .evidence_metadata import demand_comparison, evidence_metadata  # noqa: E402
from .evidence_pack import build_evidence_pack, metric_caveats  # noqa: E402
from .guide_llm import config_from_env, tool_reply  # noqa: E402
from .guide_profile import (  # noqa: E402
    COMPARE_COUNT,
    career_path,
    compact_pack,
    path_text,
    preference_sentence,
    preference_words,
    role_links,
    wants_path,
)
from .guide_tools import ToolContext  # noqa: E402
from .outreach import MESSAGE_MAX, NAME_MAX, build_draft, clean_text, employer_record  # noqa: E402
from .ranking import rank_careers  # noqa: E402
from .tts import text_to_speech, tts_status  # noqa: E402

app = FastAPI(title="Avenir app API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (4175, 5173)],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_api_route("/api/tts", text_to_speech, methods=["POST"])

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


class GuideProfile(BaseModel):
    """What the quiz gathered (or the student stated in chat); sent only when the frontend has it."""

    model_config = ConfigDict(extra="forbid")
    tags: list[Annotated[str, Field(max_length=64)]] = Field(default_factory=list, max_length=32)
    weights: Weights = Field(default_factory=Weights)
    selected: list[Annotated[str, Field(pattern=r"^\d{4}$")]] = Field(default_factory=list, max_length=5)
    free_text: str | None = Field(default=None, max_length=500)


class GuideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    soc: str = Field(pattern=r"^\d{4}$")
    message: str = Field(min_length=1, max_length=2000)
    history: list[GuideTurn] = Field(default_factory=list, max_length=30)
    profile: GuideProfile | None = None


class OutreachRequest(BaseModel):
    """A draft message to an employer's verified careers route; the student sends it themselves."""

    model_config = ConfigDict(extra="forbid")
    soc: str = Field(pattern=r"^\d{4}$")
    employer: Literal["blackrock"]
    message: str | None = Field(default=None, max_length=MESSAGE_MAX)
    name: str | None = Field(default=None, max_length=NAME_MAX)
    route: Literal["university", "apprenticeship"] = "university"

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_text(value, MESSAGE_MAX)
        if not cleaned:
            raise ValueError("message is empty once control characters and spaces are removed")
        return cleaned

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        return (clean_text(value, NAME_MAX, single_line=True) or None) if value is not None else None


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


@lru_cache(maxsize=512)
def evidence_pack(soc: str) -> dict:
    """The role's display-ready statistics pack; cached per SOC (it holds no user data)."""
    return build_evidence_pack(ml(), _career(soc))


def guide_mode() -> str:
    return "llm_grounded" if config_from_env() else "prepared_demo"


@app.get("/api/catalogue")
def catalogue() -> list[dict]:
    return catalogue_summaries(ml(), _careers())


@app.get("/api/careers/{soc}")
def career_detail(soc: str = ApiPath(pattern=r"^\d{4}$")) -> dict:
    return _career(soc)


@app.get("/api/careers/{soc}/evidence-pack")
def career_evidence_pack(soc: str = ApiPath(pattern=r"^\d{4}$")) -> dict:
    return copy.deepcopy(evidence_pack(soc))


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "careers": len(_careers()),
        "ml_mode": ml().status()["mode"],
        "guide_mode": guide_mode(),
        "guide_accepts_profile": True,
        **tts_status(),
    }


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    status = ml().status()
    fit = ml().fit()
    return {
        "careers": _careers(),
        "evidence_metadata": evidence_metadata(ml()),
        "tags": ml().tags(),
        "sources": ml().sources(),
        "backtest": ml().backtest_artefact(),
        "crises": ml().crises(),
        "data_status": {
            "mode": status["mode"],
            "artefacts": {name: details["status"] for name, details in status["artefacts"].items()},
            "origins": {name: details.get("origin") for name, details in status["artefacts"].items()},
            "fit": fit["status"],
            "fit_method": fit.get("method"),
            "fit_evaluation": fit.get("evaluation"),
            "hedges": ml().hedges_status(),
            "pathways": "curated_demo",
            "guide": guide_mode(),
            "guide_accepts_profile": True,
            **tts_status(),
            "note": (
                "Career evidence and matching use Arsenii's committed dataset and supplied affinities. "
                "The matching method and evaluation limits are supplied alongside its status. "
                "Pathways are Max's curated examples."
            ),
        },
    }


@app.post("/api/matches")
def matches(request: MatchRequest) -> dict:
    fit = ml().fit()
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
        return discover(request, _match_careers(), matches, ml().fit())
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


@app.post("/api/outreach/draft")
def outreach_draft(request: OutreachRequest) -> dict:
    """The student's message (or the alumni-kit template) addressed to the employer's verified careers
    route, with a mailto: link or the official form URL. The server never sends anything."""
    career = _career(request.soc)
    alumni = get_store().pathways["common"]["alumni"]
    template = alumni["template_apprenticeship"] if request.route == "apprenticeship" else alumni["template"]
    return build_draft(
        employer_record(request.employer),
        role=career["title"],
        template=template,
        question=alumni["questions"][0],
        message=request.message,
        name=request.name,
    )


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
    """Keep the supplied status and applicable data caveats visible in replies (same sentences as the evidence pack)."""
    notes = metric_caveats(metric)
    return " " + " ".join(notes) if notes else ""


INJECTION_REPLY = (
    "I can help explore this career: the work, pay, skills, study routes and automation evidence. "
    "Try asking what to learn first or how salaries compare after inflation."
)
GENERIC_REPLY = (
    "This prepared guide focuses on your career choice. Ask about the work, pay, skills, "
    "study routes, demand or automation evidence."
)


def _guide_reply(
    career: dict, message: str, history: list[GuideTurn], path_data: dict | None = None, words: dict | None = None
) -> tuple[str, list[str]]:
    """The prepared reply; a path question also gets the short walk through the structured path."""
    text, keys = _prepared_reply(career, message, history)
    if path_data is None or text == INJECTION_REPLY:
        return text, keys
    if text == GENERIC_REPLY:
        return path_text(career["title"], path_data, words), keys
    first_step = path_data["first_step"][:40] not in text
    return text + " " + path_text(career["title"], path_data, words, first_step=first_step), keys


def _prepared_reply(career: dict, message: str, history: list[GuideTurn]) -> tuple[str, list[str]]:
    lower = message.lower()
    # A prepared guide does not interpret instructions or generate arbitrary content.
    if re.search(
        r"ignore (all |previous |your )|system prompt|write .*(poem|story|code)|politic|recipe|weather|football|malware", lower
    ):
        return INJECTION_REPLY, []
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
        # A bridged plan borrows a whole teaching family. Its skill list is not
        # occupation-specific guidance for the requested career.
        if plan.get("related_pathway_soc"):
            return "Try this exploration exercise: " + plan["first_step"] + " " + plan["demo_note"], []
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
    return GENERIC_REPLY, []


PREPARED_NOTE = "Prepared demo guide using the supplied data and curated pathways; no live language model is connected."


def _career_path(career: dict) -> dict:
    """The structured path from the API's own data (curated plan when available, ESCO skills from the pack)."""
    plan = None
    if career.get("pathway_available"):
        try:
            plan = path(career["soc"])
        except HTTPException:
            plan = None
    return career_path(career, plan, list(evidence_pack(career["soc"]).get("skills", [])))


def _compared_packs(profile: GuideProfile | None, soc: str) -> list[dict]:
    """Compact packs (metrics and hedges) for up to COMPARE_COUNT other selected roles."""
    packs: list[dict] = []
    for other in profile.selected if profile else []:
        if other == soc or len(packs) >= COMPARE_COUNT or any(p["soc"] == other for p in packs):
            continue
        try:
            packs.append(compact_pack(evidence_pack(other)))
        except HTTPException:
            continue
    return packs


def _tool_rows() -> list[dict]:
    """Every catalogue role for `search_jobs`, with the app's display titles for the curated careers."""
    titles = {career["soc"]: career["title"] for career in _careers()}
    return [
        {"soc": o["soc2020"], "title": titles.get(o["soc2020"], o["title"]), "metrics": o["metrics"]}
        for o in ml().occupations()
    ]


def _tool_context() -> ToolContext:
    """The guide model's read-only data tools, backed by the same loaded data as the endpoints."""
    return ToolContext(pack_for=evidence_pack, occupations=_tool_rows, path_for=lambda soc: _career_path(_career(soc)))


@app.post("/api/guide")
def guide(request: GuideRequest, http_request: Request) -> dict:
    """Model-written from the role's evidence pack when a model is configured and the reply passes the hard
    checks; otherwise the prepared template. Opinions are tied to the quiz profile when one is sent; links and
    the career path are always built by the API, never by the model. A model reply is cached only under a key
    covering every input (message, history, profile, evidence, model); the prepared fallback is never cached.
    Per-IP rate limited (see rate_limit.py): 429 past the limit."""
    rate_limit.check("guide", http_request)
    career = _career(request.soc)
    pack = evidence_pack(request.soc)
    compared = _compared_packs(request.profile, request.soc)
    words = None
    if request.profile is not None:
        titles = {item["soc"]: item["title"] for item in _careers()}
        labels = {tag["id"]: tag.get("label", tag["id"]) for tag in ml().tags()}
        words = preference_words(request.profile.model_dump(), titles, labels)
    links = role_links(pack, compared)
    path_data = _career_path(career) if wants_path(request.message) else None
    extras = {
        "links": links,
        "path": path_data,
        "profile_used": words is not None,
        "compared": [item["soc"] for item in compared],
    }
    config = config_from_env()
    if config is not None:
        profile = request.profile.model_dump() if request.profile is not None else None
        evidence = guide_cache.evidence_digest(pack, compared, path_data, words, [link["label"] for link in links])
        key = guide_cache.cache_key(
            request.soc,
            request.message,
            profile,
            config.model,
            history=[turn.model_dump() for turn in request.history],
            evidence=evidence,
        )
        hit = guide_cache.load(key)
        if hit is not None:
            text, checks, tools_used = hit["text"], hit["checks"] or "passed", list(hit["tools_used"] or [])
            claims = list(hit["claims"] or [])
        else:
            text, checks, tools_used, claims = tool_reply(
                config,
                pack,
                request.message,
                request.history,
                _tool_context(),
                preferences=words,
                compared=compared,
                link_labels=[link["label"] for link in links],
                path=path_data,
            )
            if text is not None:
                guide_cache.save(
                    key,
                    {"text": text, "model": config.model, "tools_used": tools_used, "checks": checks, "claims": claims},
                )
        if text is not None:
            note = (
                "AI-written from this role's evidence pack. Each £ and % figure and each decimal or large number was "
                "matched to the same occupation, measure, unit and period in the evidence; the wording around the "
                "figures is not verified. Check the source."
            )
            if tools_used:
                note = (
                    "AI-written from this role's evidence pack and the app's data tools listed below. Each £ and % "
                    "figure and each decimal or large number was matched to the same occupation, measure, unit and "
                    "period in the evidence and tool results; the wording around the figures is not verified. "
                    "Check the source."
                )
            return {
                "text": text,
                "mode": "llm_grounded",
                "ai_written": True,
                "model": config.model,
                "sources": _source_refs([source["id"] for source in pack["sources"]]),
                "note": note,
                "based_on": list(pack["based_on"]),
                "checks": checks,
                "claims": claims,
                "tools_used": tools_used,
                "cached": hit is not None,
                **extras,
            }
        note = PREPARED_NOTE.replace("no live language model is connected", "the configured model's reply was not used")
    else:
        checks, note = "fallback: no model configured", PREPARED_NOTE
    text, keys = _guide_reply(career, request.message, request.history, path_data, words)
    if words is not None and path_data is None:
        text += " " + preference_sentence(words)
    return {
        "text": text,
        "mode": "prepared_demo",
        "ai_written": False,
        "model": None,
        "sources": _source_refs(keys),
        "note": note,
        "based_on": list(pack["based_on"]),
        "checks": checks,
        "claims": [],
        "tools_used": [],
        "cached": False,
        **extras,
    }
