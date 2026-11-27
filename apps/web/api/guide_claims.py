"""Match numeric claims to the guide's typed occupation, measure, unit and period data.

Facts come from evidence packs, paths and read-only tool results. Named measures require
the same subject, metric, unit, value and any stated period. The API returns deterministic
evidence lines for validated figures. The separate prose check still handles bare numbers
and standalone years that carry no recognised measure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from avenir_adapters.llm.writer import _canon

# Any number: optional sign (not glued to a word), £, digits with commas, decimals, % (same shape as the writer's).
_TOKEN = re.compile(r"(?<![\w.,])(?P<sign>[-+])?(?P<cur>£)?(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?(?P<pct>%)?")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_PCT_WORD = re.compile(r"^\s*(?:per ?cent|percent)\b", re.IGNORECASE)
_RELATIVE_TREND = re.compile(r"\b(?:relative to|vs\.?|compared (?:with|to)) (?:the )?typical occupation\b", re.IGNORECASE)
_GBP_WORD = re.compile(r"^\s*(?:pounds?|GBP|quid)\b", re.IGNORECASE)
_THOUSANDS_WORD = re.compile(r"^\s*(?:thousand|k)\b", re.IGNORECASE)
_SCALE = re.compile(r"^(?:\s*[–-]\s*£?\d[\d.,]*)?\s*(?:scale|point)", re.IGNORECASE)
_CLAUSE_BREAK = re.compile(r";|:|(?<!\d)\s[–—-]\s|,\s(?=\D)|\b(?:and|but|while|whereas)\b|[.!?](?=\s)", re.IGNORECASE)

# Which words say what a figure measures. The nearest one to the figure wins.
_METRIC_WORDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "starting_pay",
        re.compile(
            r"\b(?:(?:starting|graduate|entry[- ]level|trainee)\s+(?:\w+\s+)?(?:pay|salar\w*|wages?|earnings|income)"
            r"|(?:graduates?|trainees?|starters?)\s+(?:earn\w*|are paid))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pay",
        re.compile(
            r"\b(?:pay|pays|paid|salary|salaries|earn|earns|earning|earnings|wage|wages|income|median|middle half)\b",
            re.IGNORECASE,
        ),
    ),
    ("jobs", re.compile(r"\b(?:jobs|employee jobs|employed|workforce|workers|people work)\b", re.IGNORECASE)),
    (
        "trend",
        re.compile(
            r"\b(?:trend|grew|grow|grows|growth|growing|fell|fall|falls|declin\w*|rose|rise|rises|increase\w*|decrease\w*)\b",
            re.IGNORECASE,
        ),
    ),
    ("exposure", re.compile(r"\b(?:exposure|automation|automat\w*)\b", re.IGNORECASE)),
    ("similarity", re.compile(r"\b(?:similar|similarity)\b", re.IGNORECASE)),
)
# Measures the app holds no figure for: a number described this way can never be grounded.
_UNSUPPORTED = re.compile(
    r"\b(?:unemployment|inflation|employment rate|interest rate|attrition|turnover|vacancy rate|pass rate)\b", re.IGNORECASE
)
_NEGATED = re.compile(r"(?:\bnot|\bno|n['’]t|\bisn['’]t|rather than|instead of|without)\s+(?:a\s+|the\s+)?$", re.IGNORECASE)

# Evidence keys, mapped to the metric they hold. Other keys inherit their parent's metric.
_KEY_METRIC = {
    "pay": "pay",
    "median_pay": "pay",
    "pay_median": "pay",
    "pay_median_nominal": "pay",
    "pay_median_real": "pay",
    "jobs": "jobs",
    "jobs_k": "jobs",
    "trend": "trend",
    "demand_trend": "trend",
    "exposure": "exposure",
    "exposure_delta": "exposure",
    "starting_pay": "starting_pay",
    "similarity": "similarity",
}
METRIC_LABEL = {
    "pay": "median pay",
    "pay_band": "middle-half pay range endpoint",
    "starting_pay": "starting pay",
    "employer_pay": "self-reported UK base pay range endpoint",
    "jobs": "employee jobs",
    "trend": "employment trend (a year)",
    "relative_trend": "employment trend (a year relative to the typical occupation)",
    "exposure": "automation exposure (0-1 research index)",
    "similarity": "skills similarity",
}
_NO_PERIOD_KEYS = {"label", "source", "unit", "status", "flags", "caveats", "why", "evidence"}
_METRIC_PERIOD_FIELDS = {"median_pay": "pay_as_of", "trend": "trend_as_of"}
_PERIOD_FIELDS = {"as_of", "year", "period", *_METRIC_PERIOD_FIELDS.values()}


@dataclass(frozen=True)
class Fact:
    subject: str  # SOC or a specific employer and role
    metric: str  # pay, starting_pay, jobs, trend, exposure, similarity or other
    unit: str  # gbp, pct, thousand or num
    value: str  # canonical form, as a reply may write it
    years: frozenset[int]


@dataclass(frozen=True)
class Claim:
    subject: str
    occupation: str
    metric: str | None  # None when the words around the figure name no known measure
    unit: str
    value: str
    years: tuple[int, ...]
    token: str

    @property
    def period(self) -> str:
        if not self.years:
            return ""
        return str(self.years[0]) if len(self.years) == 1 else f"{self.years[0]}-{self.years[-1]}"


def format_value(value: str, unit: str) -> str:
    """The deterministic display of a canonical value: £56,914, 2.62%, 0.5444, 343."""
    try:
        number = Decimal(value)
    except InvalidOperation:
        return value
    whole, _, frac = format(number, "f").partition(".")
    sign = "-" if whole.startswith("-") else ""
    grouped = f"{int(whole.lstrip('-')):,}" + (f".{frac}" if frac else "")
    if unit == "gbp":
        return f"{sign}£{grouped}"
    if unit == "pct":
        return f"{sign}{grouped}%"
    if unit == "thousand":
        return f"{sign}{grouped} thousand"
    return f"{sign}{grouped}"


def render_claim(claim: Claim) -> str:
    """One line built only from typed fields: 'Software developer, median pay: £56,914 (2025)'."""
    label = METRIC_LABEL.get(claim.metric or "", "figure")
    period = f" ({claim.period})" if claim.period else ""
    return f"{claim.occupation}, {label}: {format_value(claim.value, claim.unit)}{period}"


def claim_dict(claim: Claim) -> dict[str, Any]:
    return {
        "soc": claim.subject if claim.subject.isdigit() else None,
        "occupation": claim.occupation,
        "metric": claim.metric,
        "period": claim.period or None,
        "unit": claim.unit,
        "value": claim.value,
        "text": render_claim(claim),
    }


def _years_in(text: str) -> set[int]:
    years: set[int] = set()
    for start, end in re.findall(r"\b((?:19|20)\d{2})\s*(?:[–—-]|\bto\b|\bthrough\b)\s*((?:19|20)\d{2})\b", text):
        if int(start) <= int(end) <= int(start) + 40:
            years |= set(range(int(start), int(end) + 1))
    return years | {int(y) for y in _YEAR.findall(text)}


def _period(value: Any) -> frozenset[int]:
    if isinstance(value, str):
        return frozenset(_years_in(value))
    if type(value) is int and 1900 <= value <= 2099:
        return frozenset({value})
    return frozenset()


def _is_year(match: re.Match[str]) -> bool:
    return not (match["sign"] or match["cur"] or match["pct"] or match["frac"]) and bool(
        re.fullmatch(r"(?:19|20)\d{2}", match["int"])
    )


def _unit(match: re.Match[str], text: str) -> str:
    suffix = text[match.end() :]
    if match["pct"] or _PCT_WORD.match(suffix):
        return "pct"
    if match["cur"] or _GBP_WORD.match(suffix):
        return "gbp"
    if _THOUSANDS_WORD.match(suffix):
        return "thousand"
    return "num"


def _canon_token(match: re.Match[str]) -> str:
    return _canon(match["int"] + (match["frac"] or ""), negative=match["sign"] == "-")


def _forms(value: float | int, metric: str) -> tuple[str, set[str]]:
    """(unit, canonical forms a reply may write) for a numeric leaf of the evidence."""
    forms: set[str] = set()
    unit = {"pay": "gbp", "starting_pay": "gbp", "trend": "pct", "relative_trend": "pct", "jobs": "thousand"}.get(metric, "num")
    scaled = Decimal(str(value))
    if unit == "pct":
        scaled = scaled * 100
    for places in (None, 0, 1, 2, 4):
        try:
            text = str(scaled) if places is None else f"{scaled:.{places}f}"
            forms.add(_canon(text))
        except (InvalidOperation, ValueError):
            continue
    return unit, forms


@dataclass
class FactBook:
    """Typed facts and occupation names read from the evidence handed to the model."""

    primary_soc: str
    facts: list[Fact] = field(default_factory=list)
    names: dict[str, set[str]] = field(default_factory=dict)
    titles: dict[str, str] = field(default_factory=dict)
    employer_roles: dict[str, tuple[str, str]] = field(default_factory=dict)

    def add(self, evidence: Any) -> FactBook:
        if isinstance(evidence, dict) and isinstance(evidence.get("employer"), str):
            self._add_employer_ranges(evidence)
        else:
            self._walk(evidence, None, "other", frozenset())
        return self

    def _add_employer_ranges(self, evidence: dict) -> None:
        employer = evidence["employer"]
        for row in (evidence.get("career_ladder_uk") or {}).get("levels", []):
            role = row["level"]
            subject = f"{employer} / {role}"
            self.employer_roles[subject] = (employer, role)
            self.titles[subject] = f"{employer} {role}"
            # The file's as-of date describes collection, not a salary period.
            for bound in ("low", "high"):
                self.facts.append(Fact(subject, "employer_pay", "gbp", _canon(str(row[bound])), frozenset()))

    def _name(self, soc: str, title: str) -> None:
        self.titles.setdefault(soc, title)
        base = re.sub(r"\s*\([^)]*\)", "", title).strip()
        self.names.setdefault(soc, set()).update(n for n in {title, base} if len(n) > 2)

    def _walk(self, node: Any, soc: str | None, metric: str, years: frozenset[int]) -> None:
        if isinstance(node, dict):
            if metric == "trend" and _RELATIVE_TREND.search(str(node.get("display", ""))):
                metric = "relative_trend"
            code = node.get("soc")
            if isinstance(code, str) and re.fullmatch(r"\d{4}", code.strip()):
                soc = code.strip()
                if isinstance(node.get("title"), str):
                    self._name(soc, node["title"])
            local = frozenset().union(*(_period(node.get(field)) for field in ("as_of", "year", "period")))
            for key, value in node.items():
                if key in _NO_PERIOD_KEYS or key in _PERIOD_FIELDS or key in ("soc", "title"):
                    continue
                metric_period = _period(node.get(_METRIC_PERIOD_FIELDS.get(key, "")))
                self._walk(value, soc, _KEY_METRIC.get(key, metric), metric_period or local or years)
        elif isinstance(node, (list, tuple)):
            for item in node:
                self._walk(item, soc, metric, years)
        elif soc is not None and metric != "other":
            if isinstance(node, str):
                if metric == "trend" and _RELATIVE_TREND.search(node):
                    metric = "relative_trend"
                shown = node.split(" (typical occupation", 1)[0]
                if metric == "pay" and "; the middle half earn " in shown:
                    shown, pay_band = shown.split("; the middle half earn ", 1)
                    self._walk(pay_band, soc, "pay_band", years or _period(shown))
                found = years or _period(shown.split(";", 1)[0])
                for match in _TOKEN.finditer(shown):
                    if not _is_year(match):
                        self.facts.append(Fact(soc, metric, _unit(match, shown), _canon_token(match), found))
            elif type(node) in (int, float):
                unit, forms = _forms(node, metric)
                self.facts.extend(Fact(soc, metric, unit, form, years) for form in forms)

    def _mentions(self, text: str) -> list[tuple[int, int, str]]:
        found: list[tuple[int, int, str]] = []
        taken: list[tuple[int, int]] = []
        pairs = sorted(((n, s) for s, names in self.names.items() for n in names), key=lambda p: -len(p[0]))
        for name, soc in pairs:
            for m in re.finditer(r"\b" + re.escape(name) + r"(?:s|es)?\b", text, re.IGNORECASE):
                if not any(m.start() < e and s < m.end() for s, e in taken):
                    taken.append((m.start(), m.end()))
                    found.append((m.start(), m.end(), soc))
        return sorted(found)

    def claims(self, text: str) -> list[Claim]:
        """Every figure in `text` as a typed claim (years and small unitless counts are left to the plain check)."""
        mentions = self._mentions(text)
        out: list[Claim] = []
        for match in _TOKEN.finditer(text):
            if _is_year(match):
                continue
            unit = _unit(match, text)
            value = _canon_token(match)
            if unit == "num" and _SCALE.match(text[match.end() :]):
                continue
            lo, hi = self._clause(text, match.start())
            metric = _metric_near(text, match.start(), match.end(), lo, hi)
            if metric == "trend" and _RELATIVE_TREND.search(text[lo:hi]):
                metric = "relative_trend"
            if metric == "pay" and re.search(r"\bmiddle half\b", text[lo:hi], re.IGNORECASE):
                metric = "pay_band"
            if metric is None and unit == "num":
                continue  # a bare number that names no measure: the plain "appears in the evidence" check covers it
            subject = self._subject(mentions, match.start(), lo, hi)
            sentence_start, sentence_end = _sentence(text, match.start())
            sentence = text[sentence_start:sentence_end]
            employer_subject = self._employer_subject(sentence)
            if employer_subject is not None:
                subject = employer_subject
                if metric == "pay" and re.search(r"\bbase pay\b", sentence, re.IGNORECASE):
                    metric = "employer_pay"
            years = tuple(sorted(_years_in(text[lo:hi])))
            out.append(Claim(subject, self.titles.get(subject, subject), metric, unit, value, years, match.group(0)))
        return out

    @staticmethod
    def _clause(text: str, pos: int) -> tuple[int, int]:
        lo, hi = 0, len(text)
        for m in _CLAUSE_BREAK.finditer(text):
            if m.end() <= pos:
                lo = m.end()
            elif m.start() >= pos:
                hi = m.start()
                break
        return lo, hi

    def _subject(self, mentions: list[tuple[int, int, str]], pos: int, lo: int, hi: int) -> str:
        inside = [(min(abs(s - pos), abs(e - pos)), s, soc) for s, e, soc in mentions if lo <= s < hi]
        if inside:
            return min(inside)[2]
        earlier = [soc for s, _e, soc in mentions if s < lo]
        return earlier[-1] if earlier else self.primary_soc

    def _employer_subject(self, sentence: str) -> str | None:
        matches = []
        occupied: list[tuple[int, int]] = []
        employer_named = False
        for subject, (employer, role) in sorted(self.employer_roles.items(), key=lambda entry: -len(entry[1][1])):
            if not re.search(r"\b" + re.escape(employer) + r"\b", sentence, re.IGNORECASE):
                continue
            employer_named = True
            for match in re.finditer(r"\b" + re.escape(role) + r"(?:s|es)?\b", sentence, re.IGNORECASE):
                if any(start <= match.start() and match.end() <= end for start, end in occupied):
                    continue
                occupied.append(match.span())
                matches.append(subject)
        if not employer_named:
            return None
        subjects = set(matches)
        return subjects.pop() if len(subjects) == 1 else "unverified employer role"


    def supported(self, claim: Claim) -> bool:
        for fact in self.facts:
            if claim.metric is None or (fact.subject, fact.metric, fact.unit) != (claim.subject, claim.metric, claim.unit):
                continue
            if claim.years and fact.years != frozenset(claim.years):
                continue
            if _same(claim.value, fact.value):
                return True
        return False

    def check(self, text: str) -> tuple[str | None, list[Claim]]:
        """(first failure or None, the claims). A failure names the figure and what it was said to measure."""
        claims = self.claims(text)
        for unsupported in _UNSUPPORTED.finditer(text):
            lo, hi = self._clause(text, unsupported.start())
            for match in _TOKEN.finditer(text[lo:hi]):
                if _unit(match, text[lo:hi]) != "num":
                    measure = unsupported.group(0).lower()
                    return f"figure {match.group(0)} described as {measure}, which the evidence does not hold", claims
        for claim in claims:
            if not self.supported(claim):
                what = METRIC_LABEL.get(claim.metric or "", "a figure")
                period = f" in {claim.period}" if claim.period else ""
                return f"figure {claim.token} is not the {what} of {claim.occupation}{period} in the evidence", claims
        return None, claims


def _same(a: str, b: str) -> bool:
    """Equal as written, or `a` is `b` correctly rounded to a's own decimals (never more precise than the evidence)."""
    if a == b:
        return True
    try:
        left, right = Decimal(a), Decimal(b)
    except InvalidOperation:
        return False
    places = max(-left.as_tuple().exponent, 0)
    if -right.as_tuple().exponent <= places or (places == 0 and abs(right) < 100):
        return False
    return right.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP) == left


def _metric_near(text: str, start: int, end: int, lo: int, hi: int) -> str | None:
    """The measure named closest to the figure: in its clause first, then the whole sentence."""
    for a, b in ((lo, hi), _sentence(text, start)):
        best: tuple[int, str] | None = None
        for metric, pattern in _METRIC_WORDS:
            for m in pattern.finditer(text, a, b):
                if metric == "starting_pay" and _NEGATED.search(text[max(a, m.start() - 24) : m.start()]):
                    continue
                dist = min(abs(m.start() - end), abs(start - m.end()))
                if best is None or dist < best[0]:
                    best = (dist, metric)
        if best:
            return best[1]
    return None


def _sentence(text: str, pos: int) -> tuple[int, int]:
    lo = max(text.rfind(". ", 0, pos), text.rfind("\n", 0, pos)) + 1
    hi = text.find(". ", pos)
    return lo, len(text) if hi < 0 else hi
