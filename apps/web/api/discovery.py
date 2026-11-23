"""Deterministic onboarding extraction over supplied career evidence; no I/O."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .ranking import rank_careers


class DiscoveryAnswers(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    direction: str = Field(default="", max_length=1000)
    interests: str = Field(default="", max_length=2000)
    subjects: str = Field(default="", max_length=1000)
    values: str = Field(default="", max_length=1000)
    skills: str = Field(default="", max_length=2000)

    def text(self) -> str:
        return "\n".join(self.model_dump().values())

    def activity_text(self) -> str:
        return "\n".join((self.direction, self.interests, self.subjects, self.skills))

    def positive_activity_text(self) -> str:
        return _positive_clauses(self.activity_text())


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["known", "explore"]
    answers: DiscoveryAnswers


ALIASES = {
    "2134": ("software engineer", "software developer", "programmer", "coder", "app developer"),
    "3544": ("data analyst", "data scientist"),
    "2133": ("business analyst", "systems designer", "systems analyst", "it analyst"),
    "2135": ("cybersecurity", "cyber security", "ethical hacker", "security analyst"),
    "2141": ("web designer", "web developer", "ux designer"),
    "2142": ("graphic designer", "graphic design", "multimedia designer", "illustrator", "animator"),
    "2451": ("architect", "architecture"),
    "2452": ("town planner", "planning officer"),
    "3120": ("cad technician", "architectural technician", "draughtsperson"),
    "2121": ("civil engineer", "civil engineering"),
    "2123": ("electrical engineer", "electrical engineering", "power engineer"),
    "3113": ("engineering technician",),
    "2453": ("quantity surveyor", "quantity surveying"),
    "2454": ("chartered surveyor", "land surveyor", "surveying"),
    "2433": ("actuary", "economist", "statistician", "quantitative analyst", "quant analyst"),
    "2422": ("investment analyst", "financial analyst", "investment adviser"),
    "2421": ("accountant", "accounting"),
    "2254": ("radiographer", "radiography"),
    "5241": ("electrician", "electrical fitter"),
    "2313": ("teacher", "teaching"),
}

# These expand ordinary language into the EXISTING supplied tag vocabulary.
# They do not add career affinities, personality scores or quantitative evidence.
SYNONYMS = {
    "maths": r"\b(mathematics|statistics|stats|numeracy|calculus)\b",
    "computers_coding": r"\b(cs|computing|computer science|programming|software engineering)\b",
    "data": r"\b(spreadsheets?|statistics|stats|analytical|attention to detail)\b",
    "design": r"\b(creativity|creative|imaginative|visual thinking|digital art)\b",
    "art_drawing": r"\b(fine art|illustration|sketching)\b",
    "building_spaces": r"\b(architecture|urban planning|built environment)\b",
    "engineering_making": r"\b(woodwork|robotics|mechanical|making things|design technology)\b",
    "fixing_hands_on": r"\b(practical work|hands on|repairing|fixing|workshop)\b",
    "electricity_energy": r"\b(electronics|renewables|power systems)\b",
    "science_health": r"\b(chemistry|biomedical|anatomy|healthcare|medicine)\b",
    "helping_people": r"\b(helping people|caring|listening|supporting others|volunteering)\b",
    "teaching_explaining": r"\b(explaining|presenting|communication|tutoring|mentoring)\b",
    "money_business": r"\b(economics|entrepreneurship|accounting|commerce)\b",
    "security_puzzles": r"\b(problem solving|logical puzzles|cryptography)\b",
    "writing_language": r"\b(literature|humanities|essay writing|storytelling|languages)\b",
    "outdoors_maps": r"\b(geography|geology|fieldwork|orienteering)\b",
}


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _positive_clauses(text: str) -> str:
    """Ignore plainly negated clauses rather than counting disliked activities.

    This intentionally handles explicit wording only, not general sentiment.
    A contrast such as "dislike coding, but enjoy helping" keeps the latter.
    """
    clauses = re.split(
        r"[,;.!?\n]|\b(?:but|however|although|yet)\b|\band\s+(?=(?:i\s+)?(?:enjoy|like|love|prefer)\b)",
        text.lower().replace("’", "'"),
    )
    negative = (
        r"\b(?:dislike|hate|avoid|not interested in|not keen on|no interest in|"
        r"(?:do not|don't|never)\s+(?:like|enjoy|want|prefer)|"
        r"(?:do not|don't|does not|doesn't|am not|i'm not|not)\s+(?:really\s+|that\s+|too\s+)?"
        r"(?:care|mind|bothered|fussed|worried)|"
        r"(?:do not|don't|does not|doesn't)\s+(?:really\s+)?matter|"
        r"(?:not|isn't|aren't)\s+(?:very\s+|that\s+|so\s+)?(?:important|a priority)|"
        r"unimportant|irrelevant|not a concern)\b"
    )
    return " ".join(clause for clause in clauses if not re.search(negative, clause))


def _contains(text: str, phrase: str) -> bool:
    return bool(re.search(r"\b" + re.escape(_normalise(phrase)) + r"\b", text))


def _resolve(direction: str, careers: list[dict]) -> str | None:
    text = _normalise(_positive_clauses(direction))
    matches = []
    for career in careers:
        soc = career["soc"]
        names = (career["title"], *ALIASES.get(soc, ()))
        for name in names:
            if _contains(text, name):
                matches.append((len(_normalise(name)), soc))
    if not matches:
        return None
    # A specific role name wins over a short word embedded in that role.
    return sorted(matches, key=lambda match: (-match[0], match[1]))[0][1]


def _weights(values: str) -> tuple[dict[str, int], str | None]:
    text = values.lower()
    financial = bool(re.search(r"\b(pay|salary|income|earning|earnings|money|financial|well paid)\b", text))
    stability = bool(
        re.search(r"\b(stable|stability|job security|secure job|reliable work|employment security|long[- ]term demand)\b", text)
    )
    if financial and stability:
        weights = {"pay": 25, "interest": 50, "need": 25}
    elif financial:
        weights = {"pay": 30, "interest": 55, "need": 15}
    elif stability:
        weights = {"pay": 15, "interest": 55, "need": 30}
    else:
        return {"pay": 15, "interest": 70, "need": 15}, None
    return weights, (
        f"Your stated priorities set the comparison weights to interest {weights['interest']}%, "
        f"pay {weights['pay']}% and observed demand {weights['need']}%. "
        "Demand is historical evidence, not a guarantee of job security."
    )


def discover(request: DiscoveryRequest, careers: list[dict], tag_matches: list[dict], fit: dict) -> dict:
    """Build comparisons from evidence and ML matches on positive activity text."""
    if len(careers) < 3:
        raise ValueError("At least three career profiles are needed to compare options.")
    affinity = fit["affinity"]
    activity = request.answers.positive_activity_text()
    # The ML matcher owns its keyword/stem syntax. It receives only positive
    # activities; value-only salary preferences affect weights, not interests.
    selected = {match["tag"] for match in tag_matches if match["tag"] in affinity}
    for tag, pattern in SYNONYMS.items():
        if tag in affinity and re.search(pattern, activity):
            selected.add(tag)
    notices = []
    target = _resolve(request.answers.direction, careers) if request.mode == "known" else None
    related = None
    if target is not None:
        if not selected:
            strongest = sorted(affinity, key=lambda tag: (-affinity[tag].get(target, 0), tag))
            selected.update(tag for tag in strongest[:3] if affinity[tag].get(target, 0) > 0)
            notices.append("With only a career direction supplied, comparison interests come from its supplied affinity profile.")
        title = next(career["title"] for career in careers if career["soc"] == target)
        notices.append(f"{title} stays first as your reference career; the next two options are ranked comparisons.")
    elif request.mode == "known" and request.answers.direction.strip():
        if re.search(r"\barchitectural technologist\b", activity):
            selected.update(tag for tag in ("building_spaces", "design") if tag in affinity)
            related = "2452" if any(career["soc"] == "2452" for career in careers) else None
            notices.append(
                "Architectural technologists are included in the broad SOC 2452 occupation group alongside planning roles. "
                "This grouped profile is a reference, not an exact role-specific estimate; training routes differ."
            )
        elif re.search(r"\b(doctor|physician|surgeon|nurse|dentist|physiotherapist|vet|veterinarian)\b", activity):
            selected.update(tag for tag in ("science_health", "helping_people") if tag in affinity)
            related = "2254" if any(career["soc"] == "2254" for career in careers) else None
            notices.append(
                "Your requested clinical career is not in this career collection. Medical radiographer is a related "
                "healthcare option, not an exact match; its training and day-to-day work differ."
            )
        else:
            notices.append(
                "There is no exact career-title match in this collection; these options compare the interests you shared."
            )
    if not selected:
        raise ValueError(
            "Tell us about one subject or activity you enjoy, or name a career in the collection, to compare options."
        )
    weights, weight_note = _weights(_positive_clauses(request.answers.values))
    if weight_note:
        notices.append(weight_note)
    if fit.get("evaluation", {}).get("note"):
        notices.append(fit["evaluation"]["note"])
    elif fit.get("status") == "mock":
        notices.append("Interest matching uses the supplied sample affinities; treat these as exploration prompts.")
    tags = sorted(selected)
    ranked = rank_careers(careers, tags, weights, affinity, fit_status=fit.get("status", "mock"))
    reference = target or related
    if reference:
        ranked = [next(career for career in ranked if career["soc"] == reference)] + [
            career for career in ranked if career["soc"] != reference
        ]
    labels = {tag["id"]: tag["label"] for tag in fit.get("tags", [])}
    summary = "Your answers connect with " + ", ".join(labels.get(tag, tag.replace("_", " ")).lower() for tag in tags[:5]) + "."
    return {
        "results": ranked[:3],
        "tags": tags,
        "target_soc": target,
        "reference_soc": reference,
        "profile_summary": summary,
        "notices": notices,
        "weights": weights,
        "method": (
            "Deterministic keyword and synonym mapping to supplied interest tags, then supplied affinity scores "
            "combined with pay and observed demand percentiles. This is career exploration, not a psychological diagnosis."
        ),
    }
