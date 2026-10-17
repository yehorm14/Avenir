"""Radar: what is open in your fields, and the trend check.

The opportunities feed is a curated snapshot of real organisers and programme
types with typical timing windows. It carries no invented dates. A programme is
'open' when this month is in its usual opening months, 'soon' when next month
is, and 'rolling' when it runs all year. Live dated feeds would replace the
snapshot through the adapter in adapters/__init__.py.
"""

from __future__ import annotations

from datetime import date

from .data import Store
from .models import CareerRef, Digest, FieldInfo, Opportunity, Radar, Trend, TrendChoice
from .path import doors_for

STAGES = ("school", "college", "university")
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland")
ORDER = {"open": 0, "soon": 1, "rolling": 2, "later": 3}
NOTE = (
    "Dated live feeds (employer careers pages, event listings) are not connected yet, so this uses each programme's "
    "usual timing. It refreshes every day you open it. Always confirm dates and eligibility on the organiser's site."
)
TREND_NOTE = (
    "'Heat' is a curated, qualitative note. Real job-advert demand data is not connected yet. "
    "The doors each broader degree opens are counted from our own careers data."
)


def status_for(opp: dict, month: int, today: date | None = None) -> str | None:
    """Status from exact dates when a live feed supplies them, otherwise from typical months.
    Returns None for an opportunity whose deadline has passed."""
    if today and (opp.get("deadline") or opp.get("opens")):
        if opp.get("deadline") and today > date.fromisoformat(opp["deadline"]):
            return None
        if opp.get("opens") and today < date.fromisoformat(opp["opens"]):
            return "soon" if (date.fromisoformat(opp["opens"]) - today).days <= 31 else "later"
        return "open"
    if opp.get("rolling"):
        return "rolling"
    months = set(opp.get("open_months", []))
    if month in months:
        return "open"
    if month % 12 + 1 in months:
        return "soon"
    return "later"


def radar(store: Store, fields: list[str], stage: str, nation: str, today: date | None = None) -> Radar:
    today = today or date.today()
    labels = store.field_labels
    stage = stage if stage in STAGES else "school"
    nation = nation if nation in NATIONS else "England"
    chosen = [f for f in dict.fromkeys(fields) if f in labels]

    items: list[Opportunity] = []
    for o in store.opportunities:
        if "UK" not in o["nations"] and nation not in o["nations"]:
            continue
        if stage not in o["stage"]:
            continue
        everywhere = "all" in o["fields"]
        hit = [f for f in chosen if f in o["fields"]]
        if chosen and not everywhere and not hit:
            continue
        status = status_for(o, today.month, today)
        if status is None:
            continue  # the deadline has passed
        closing = bool(o.get("deadline")) and (date.fromisoformat(o["deadline"]) - today).days <= 14
        matches = [labels[f] for f in hit] if hit else (["Any field"] if everywhere else [])
        items.append(Opportunity(**{**o, "status": status, "matches": matches, "closing_soon": closing}))
    items.sort(key=lambda i: (ORDER[i.status], -len(i.matches), i.title))

    n = {k: sum(1 for i in items if i.status == k) for k in ORDER}
    where = ", ".join(labels[f].lower() for f in chosen[:3]) if chosen else "all fields"
    if n["open"] or n["soon"]:
        headline = f"{n['open']} in their usual opening window this month and {n['soon']} opening next month, plus {n['rolling']} you can start any time ({where})."
    else:
        headline = f"Nothing is in its usual opening window this month in {where}, but {n['rolling']} things are open all year."
    pool = [i for i in items if i.status in ("open", "soon")] or [i for i in items if i.status == "rolling"]
    highlights = [f"{i.title} ({i.org})" for i in pool[:3]]
    return Radar(
        today=today.isoformat(), month=today.month, stage=stage, nation=nation,
        fields=[FieldInfo(id=f, label=labels[f]) for f in chosen],
        all_fields=[FieldInfo(id=k, label=v) for k, v in labels.items()],
        digest=Digest(headline=headline, open=n["open"], soon=n["soon"], rolling=n["rolling"], later=n["later"], highlights=highlights),
        items=items, live=False, note=NOTE,
    )


def trends(store: Store) -> list[Trend]:
    out = []
    for t in store.pathways["specialisms"]:
        out.append(Trend(
            id=t["id"], name=t["name"], heat=t["heat"], buzz=t["buzz"], reality=t["reality"],
            specialist_name=t["specialist"]["name"], specialist_level=t["specialist"]["level"], specialist_doors=t["specialist"]["doors"],
            safer=[TrendChoice(subject=s["subject"], why=s["why"], doors=doors_for(store, s["subject"])) for s in t["safer"]],
            fade=t["fade"], how=t["how"],
            related=[CareerRef(soc=s, title=store.occupations[s].title) for s in t["related"] if s in store.occupations],
            evidence_note=TREND_NOTE,
        ))
    return out
