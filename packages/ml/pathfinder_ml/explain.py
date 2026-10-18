"""Plain-English explanations that cannot invent numbers. Standard library only.

Two tools for the AI/glue slice:
- template_explanation(occupation): deterministic prose from an occupation record (the fallback
  when the LLM is down, and the reference the LLM's draft is checked against).
- validate_explanation(text, occupation): checks that every number in a draft matches a number
  in the record (within display rounding) and that every MUST_MENTION flag on a metric with a
  value is mentioned. Returns a list of problems; empty means the draft may be shown.

Usage pattern: draft = llm(prompt_with(numbers, FLAG_TEXT)); problems = validate_explanation(draft, occ);
show draft if not problems else template_explanation(occ)["text"].
"""
from __future__ import annotations

import re

from .api import FLAG_TEXT, MUST_MENTION

# Words that count as mentioning a flag (any one phrase is enough, case-insensitive).
FLAG_KEYWORDS = {
    "bridged_soc2010": ["older occupation codes", "soc 2010", "estimated from the older", "crosswalk", "before 2021 are estimated"],
    "bridged_soc2000": ["soc 2000", "before 2011 are estimated", "two ons crosswalks", "older occupation codes"],
    "recoded_2021": ["2021", "codes changed", "not directly comparable"],
    "covid_year": ["pandemic", "covid", "furlough", "2020 figures"],
    "employees_only": ["employees only", "self-employed", "freelance"],
    "imputed_parent": ["wider occupation group", "wider group", "estimated from the wider", "group-level", "estimate"],
    "category_level": ["category", "broad job-advert"],
    "sources_disagree": ["disagree", "two research estimates", "sources differ"],
    "bridged_low_purity": ["mixed several different jobs", "may not describe this job", "older occupation code"],
    "ons_indicative_counts": ["indicative", "not accurate estimates"],
    "mock": ["sample data", "not a real figure"],
}

_NUMBER = re.compile(r"(?<![\d.])[-+]?\d[\d,]*(?:\.\d+)?(?!\d)")
_YEAR_RANGE = re.compile(r"\b((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)?\d{2})\b")


def fmt(metric: dict) -> str | None:
    v = metric.get("value")
    if v is None:
        return None
    unit = metric.get("unit")
    if unit == "GBP/year":
        return f"£{v:,.0f}"
    if unit == "thousand jobs":
        return f"{v * 1000:,.0f} jobs"
    if unit == "fraction":
        return f"{v * 100:+.1f}%"
    if unit == "fraction/year":
        return f"{v * 100:+.1f}% a year"
    if unit == "score 0-1":
        return f"{v:.2f} on a 0 to 1 scale"
    return f"{v}"


def _flags_in_use(occ: dict) -> list[str]:
    flags = []
    for m in occ["metrics"].values():
        if m.get("value") is None:
            continue
        for f in m.get("flags", []):
            if f in MUST_MENTION and f not in flags:
                flags.append(f)
    return flags


def template_explanation(occ: dict, crises_on_card: tuple[str, ...] = ("resilience_covid", "resilience_tech_slump")) -> dict:
    """Deterministic explanation of one occupation card: numbers from the record, flags spelled out.
    crises_on_card: resilience metrics to mention (crises.json show_on_card; 2008 and cost of living fail the placebo test)."""
    on_card = crises_on_card
    m = occ["metrics"]
    title = occ.get("short_title") or occ.get("title")
    parts, used = [], []

    def use(key: str) -> dict | None:
        met = m.get(key)
        if met and met.get("value") is not None:
            used.append(key)
            return met
        return None

    pay = use("pay_median")
    if pay:
        s = f"{title}s earn a median of {fmt(pay)} a year (full-time employees, {pay['as_of']})"
        if pay.get("low") is not None and pay.get("high") is not None:
            s += f"; the middle half earn between £{pay['low']:,.0f} and £{pay['high']:,.0f}"
        parts.append(s + ".")
    rp = use("real_pay_change_10y")
    if rp:
        parts.append(f"After inflation, pay changed by {fmt(rp)} between 2015 and 2025.")
    dt = use("demand_trend")
    if dt:
        parts.append(f"Compared with the typical occupation, the number of jobs has been changing by about {fmt(dt)} since 2022"
                     + (f" (range {dt['low'] * 100:+.1f}% to {dt['high'] * 100:+.1f}%)" if dt.get("low") is not None and dt.get("high") is not None else "") + ".")
    ex = use("exposure")
    if ex:
        grad = (ex.get("extra") or {}).get("gradient")
        parts.append(f"Automation exposure is {fmt(ex)}" + (f", which the ILO classes as '{grad}'" if grad else "")
                     + "; this is a research estimate of how many tasks generative AI could touch, not a prediction that the job disappears.")
    crises = [(k, m[k]) for k in on_card if m.get(k, {}).get("value") is not None]
    if crises:
        labels = {"resilience_covid": "the pandemic", "resilience_cost_of_living": "the recovery after the cost-of-living shock", "resilience_tech_slump": "the 2022-24 hiring slump", "resilience_2008": "the 2008 crisis"}
        best = max(crises, key=lambda kv: kv[1]["value"])
        worst = min(crises, key=lambda kv: kv[1]["value"])
        used.extend([best[0], worst[0]])
        parts.append(f"Compared with the typical occupation it held up best in {labels[best[0]]} ({fmt(best[1])}) and worst in {labels[worst[0]]} ({fmt(worst[1])}).")
    yw = use("young_worker_share")
    if yw:
        parts.append(f"In 2016, {yw['value'] * 100:.0f}% of people in this job were under 25.")
    flags = _flags_in_use(occ)
    if flags:
        parts.append("Caveats: " + " ".join(FLAG_TEXT[f] for f in flags))
    return {"text": " ".join(parts), "metrics_used": used, "flags_mentioned": flags}


def allowed_numbers(occ: dict) -> list[float]:
    """Every number a draft may cite: metric values, ranges, their percentage forms, the years in as_of."""
    nums: list[float] = []
    for met in occ["metrics"].values():
        for k in ("value", "low", "high"):
            v = met.get(k)
            if v is None:
                continue
            nums.append(float(v))
            if met.get("unit") in ("fraction", "fraction/year"):
                nums.append(float(v) * 100)
            if met.get("unit") == "thousand jobs":
                nums.append(float(v) * 1000)
        for y in re.findall(r"\d{4}", str(met.get("as_of", ""))):
            nums.append(float(y))
        # Numbers that are part of the metric's own definition ("aged 16 to 24", "25th to 75th percentile").
        for n in re.findall(r"\d+(?:\.\d+)?", str(met.get("note", ""))):
            nums.append(float(n))
        for v in (met.get("extra") or {}).values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                nums.append(float(v))
                nums.append(float(v) * 100)
    for sentence in FLAG_TEXT.values():  # the caveat sentences themselves ("SOC 2010", "2021")
        nums.extend(float(n) for n in re.findall(r"\d+(?:\.\d+)?", sentence))
    nums.extend(float(i) for i in range(0, 11))  # "top 3", "one in ten", ordinal small numbers
    return nums


def _matches(cited: float, allowed: list[float], text_precision: int) -> bool:
    tol = 0.5 * 10 ** (-text_precision) + 1e-9
    return any(abs(cited - a) <= tol + abs(a) * 0.0005 for a in allowed)


def validate_explanation(text: str, occ: dict) -> list[str]:
    """Return problems with a draft: invented numbers and unmentioned MUST_MENTION flags."""
    problems = []
    allowed = allowed_numbers(occ)
    # Year ranges such as "2022-24" or "2015 to 2025" are checked as years, not as free numbers.
    for a, b in _YEAR_RANGE.findall(text):
        b_full = b if len(b) == 4 else a[:2] + b
        for y in (a, b_full):
            if float(y) not in allowed:
                problems.append(f"year not in the record: {y}")
    scrubbed = _YEAR_RANGE.sub(" ", text)
    for raw in _NUMBER.findall(scrubbed):
        clean = raw.replace(",", "").rstrip(".")
        if not clean or clean in ("-", "+"):
            continue
        try:
            val = float(clean)
        except ValueError:
            continue
        precision = len(clean.split(".")[1]) if "." in clean else 0
        if not _matches(val, allowed, precision):
            problems.append(f"number not in the record: {raw}")
    lower = text.lower()
    for f in _flags_in_use(occ):
        if not any(k in lower for k in FLAG_KEYWORDS[f]):
            problems.append(f"flag not mentioned: {f} ({FLAG_TEXT[f]})")
    return problems
