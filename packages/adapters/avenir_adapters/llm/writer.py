"""LLM-written explanation with hard checks; any problem falls back to the template.

The text is accepted only if every number in it appears in the response (`allowed_numbers`),
every notice sentence is copied verbatim, and it avoids the banned phrases. `explain()` never raises.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from avenir_contracts.models import Explanation, RecommendationOut
from avenir_contracts.ports import ExplanationWriter, TemplateExplanation

MIN_RETRY_SECONDS = 0.5
BANNED_PHRASES = ("you should", "don't", "don’t")
TRUTHY = {"1", "true", "yes"}

SYSTEM_PROMPT = (
    "You write a short career explanation for a 17-year-old in the UK. "
    "Use plain English and fewer than 120 words. Say careers are \"worth exploring\". "
    "Never use the phrases \"you should\" or \"don't\". "
    "Use only numbers that appear in the data you are given; never add or round numbers yourself. "
    "Copy each notice sentence word for word."
)

# optional sign (not glued to a word), optional £, digits with optional thousands commas, optional decimals
_NUMBER = re.compile(r"(?<![\w.,])(?P<sign>[-+])?£?(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?%?")


def _canon(s: str, negative: bool = False) -> str:
    d = Decimal(s.replace(",", ""))
    out = format(d, "f")
    if "." in out:
        out = out.rstrip("0").rstrip(".")
    if out in ("", "-0"):
        out = "0"
    if negative and not out.startswith("-") and out != "0":
        out = "-" + out
    return out


def numbers_in(text: str) -> set[str]:
    """Numeric tokens in `text`, normalised: no £ , % or leading +; trailing zeros dropped; '-' kept."""
    found: set[str] = set()
    for m in _NUMBER.finditer(text):
        try:
            found.add(_canon(m["int"] + (m["frac"] or ""), negative=m["sign"] == "-"))
        except InvalidOperation:  # pragma: no cover - the regex only yields valid decimals
            continue
    return found


def _walk(obj: Any):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk(v)
    else:
        yield obj


def allowed_numbers(rec: RecommendationOut) -> set[str]:
    """Every number the model may cite: values in `rec` as the templates print them, plus numbers in its strings."""
    allowed: set[str] = set()
    for v in _walk(rec.model_dump()):
        if isinstance(v, str):
            allowed |= numbers_in(v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            for places in (0, 1, 2):
                allowed.add(_canon(f"{v:.{places}f}"))
            if abs(v) <= 1:
                for places in (0, 1):
                    allowed.add(_canon(f"{v * 100:.{places}f}"))
    return allowed


def _summary(rec: RecommendationOut) -> dict[str, Any]:
    out: dict[str, Any] = {
        "first_idea": rec.first_idea.title if rec.first_idea else None,
        "picks": [{"tier": p.tier, "title": p.career.title, "reasons": p.reasons} for p in rec.picks],
        "hedge": rec.hedge.career.title if rec.hedge else None,
        "this_month": rec.roadmap.this_month if rec.roadmap else None,
        "notices": rec.notices,
    }
    return out


class LlmExplanation:
    """ExplanationWriter over an OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._fallback = TemplateExplanation()

    def explain(self, rec: RecommendationOut) -> Explanation:
        try:
            text = self._complete(rec)
            if text and self._passes(text, rec):
                return Explanation(text=text, ai_written=True, cited_numbers=sorted(numbers_in(text)))
        except Exception:  # never raise: any failure means the template
            pass
        return self._fallback.explain(rec)

    def _complete(self, rec: RecommendationOut) -> str | None:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(_summary(rec), ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        start = time.monotonic()
        for attempt in range(2):
            remaining = self.timeout - (time.monotonic() - start)
            if remaining <= 0 or (attempt == 1 and remaining < MIN_RETRY_SECONDS):
                return None
            try:
                resp = requests.post(f"{self.base_url}/chat/completions", headers=headers,
                                     json=payload, timeout=remaining)
                if 200 <= resp.status_code < 300:
                    content = resp.json()["choices"][0]["message"]["content"]
                    return content.strip() if isinstance(content, str) else None
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
                pass
        return None

    @staticmethod
    def _passes(text: str, rec: RecommendationOut) -> bool:
        if numbers_in(text) - allowed_numbers(rec):
            return False
        if any(n not in text for n in rec.notices):
            return False
        lowered = text.lower()
        return not any(p in lowered for p in BANNED_PHRASES)


def writer_from_env(env: Mapping[str, str] | None = None) -> ExplanationWriter:
    """LlmExplanation only when LLM_ENABLED is truthy and base URL, key and model are all set."""
    env = os.environ if env is None else env
    enabled = env.get("LLM_ENABLED", "").strip().lower() in TRUTHY
    base, key, model = (env.get(k, "").strip() for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"))
    if enabled and base and key and model:
        return LlmExplanation(base, key, model)
    return TemplateExplanation()
