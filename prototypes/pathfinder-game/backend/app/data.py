"""Joins every source on the SOC 2020 code into one in-memory store."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .adapters import ADAPTERS, SourceAdapter

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RIASEC = ("R", "I", "A", "S", "E", "C")

SUBJECTS = [
    "Maths", "English", "Physics", "Chemistry", "Biology", "Computing",
    "Engineering or Design and Technology", "Art and Design", "Music", "Drama",
    "History", "Geography", "Modern Languages", "Business or Economics",
    "Psychology", "Politics or Modern Studies", "PE", "Health and Social Care",
    "Food or Hospitality",
]

SKILLS = [
    "Coding", "Fixing things", "Building or making things", "Drawing or design",
    "Writing", "Spreadsheets or data", "Caring for someone", "Volunteering",
    "Customer service job", "First aid", "Team leader or captain", "Sport coaching",
    "Public speaking or debating", "Languages", "Working with animals",
    "Lab or science club",
]


@dataclass
class Occupation:
    soc: str
    title: str
    soc_title: str
    summary: str
    study_level: str
    subjects: list[str]
    skills_have: list[str]
    first_step: str
    onet_code: str | None = None
    onet_title: str | None = None
    riasec: list[float] | None = None
    growth_2035_pct: float | None = None
    priority: bool | None = None
    sector: str | None = None
    ssv: dict[str, float | None] = field(default_factory=dict)
    routes: list[dict] = field(default_factory=list)
    skills_build: list[str] = field(default_factory=list)
    courses: list[dict] = field(default_factory=list)
    pay: dict | None = None
    ai_tasks: list[dict] = field(default_factory=list)
    nation_routes: dict[str, list[dict]] = field(default_factory=dict)

    @property
    def ai_exposure(self) -> float | None:
        if not self.ai_tasks:
            return None
        return round(sum(t["score"] for t in self.ai_tasks) / len(self.ai_tasks), 3)

    @property
    def pay_median(self) -> float | None:
        return self.pay.get("median") if self.pay else None


@dataclass
class Store:
    occupations: dict[str, Occupation]
    adapters: dict[str, SourceAdapter]
    ess_editions: list[str]
    quiz: dict
    regions: dict[str, dict]
    backtest: dict
    pay_edition: str | None
    pay_previous_edition: str | None
    pathways: dict
    family_of: dict[str, str]
    opportunities: list[dict]
    field_labels: dict[str, str]
    pay_series: dict
    cpi: dict

    @property
    def latest_ess(self) -> str:
        return self.ess_editions[-1]

    @property
    def previous_ess(self) -> str:
        return self.ess_editions[-2]


@lru_cache(maxsize=1)
def get_store() -> Store:
    adapters = {a.info.id: a for a in ADAPTERS}
    payload = {k: a.load() for k, a in adapters.items()}

    with open(DATA_DIR / "occupations.json", encoding="utf-8") as f:
        core = json.load(f)["occupations"]
    with open(DATA_DIR / "quiz.json", encoding="utf-8") as f:
        quiz = json.load(f)

    onet = payload["onet"].get("occupations", {})
    se = payload["skills_england"].get("occupations", {})
    ess = payload["ess"].get("editions", {})
    maps = payload["occupational_maps"].get("occupations", {})
    uni = payload["discover_uni"].get("occupations", {})
    ashe = payload["ashe"].get("occupations", {})
    ai = payload["ai_exposure"].get("occupations", {})
    nations = payload["nations"].get("occupations", {})
    editions = sorted(ess)

    occupations: dict[str, Occupation] = {}
    for row in core:
        soc = row["soc"]
        occ = Occupation(
            soc=soc,
            title=row["title"],
            soc_title=row["soc_title"],
            summary=row["summary"],
            study_level=row["study_level"],
            subjects=row["subjects"],
            skills_have=row["skills"],
            first_step=row["first_step"],
        )
        if soc in onet:
            occ.onet_code = onet[soc]["onet_code"]
            occ.onet_title = onet[soc]["onet_title"]
            occ.riasec = onet[soc]["riasec"]
        if soc in se:
            occ.growth_2035_pct = se[soc].get("growth_2035_pct")
            occ.priority = se[soc].get("priority")
            occ.sector = se[soc].get("sector")
        occ.ssv = {ed: ess[ed].get(soc) for ed in editions}
        if soc in maps:
            occ.routes = maps[soc].get("routes", [])
            occ.skills_build = maps[soc].get("skills", [])
        occ.courses = uni.get(soc, [])
        occ.pay = ashe.get(soc)
        occ.ai_tasks = ai.get(soc, [])
        occ.nation_routes = nations.get(soc, {})
        occupations[soc] = occ

    pw = DATA_DIR / "pathways"
    pathways = {}
    for key, name in (("subjects", "subjects.json"), ("families", "families.json"), ("common", "common.json")):
        with open(pw / name, encoding="utf-8") as f:
            pathways[key] = json.load(f)
    with open(pw / "specialisms.json", encoding="utf-8") as f:
        pathways["specialisms"] = json.load(f)["specialisms"]
    pathways["subjects"] = pathways["subjects"]["subjects"]
    pathways["families"] = pathways["families"]["families"]
    family_of = {soc: fid for fid, fam in pathways["families"].items() for soc in fam["socs"]}

    return Store(
        occupations=occupations,
        adapters=adapters,
        ess_editions=editions,
        quiz=quiz,
        regions=payload["regions"].get("regions", {"UK-wide": {"nation": "UK", "multipliers": {}}}),
        backtest=payload["backtest"],
        pay_edition=payload["ashe"].get("edition"),
        pay_previous_edition=payload["ashe"].get("previous_edition"),
        pathways=pathways,
        family_of=family_of,
        opportunities=payload["opportunities"].get("opportunities", []),
        field_labels=payload["opportunities"].get("fields", {}),
        pay_series=payload["ashe_series"],
        cpi=payload["cpi"],
    )
