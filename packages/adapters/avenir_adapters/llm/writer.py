"""LLM-written explanation with hard checks; any problem falls back to the template.

The text is accepted only if every number in it appears in the response (`allowed_numbers`),
every notice sentence is copied verbatim, and it avoids the banned phrases and spelled-out numbers.
`explain()` never raises and returns within `timeout` seconds in total (a hard wall-clock limit, see
`_deadline`). After a timeout, connection error or HTTP 401/403/429 the model is skipped for `BREAKER_S`.
Logs carry only the fallback reason (exception type, HTTP status or the failed check), never the key,
URL, prompt or response text.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from avenir_adapters._deadline import DeadlineExceeded, call_with_deadline
from avenir_contracts.models import Explanation, RecommendationOut
from avenir_contracts.ports import ExplanationWriter, TemplateExplanation

log = logging.getLogger(__name__)

MIN_RETRY_SECONDS = 0.5
BREAKER_S = 60.0
BANNED_PHRASES = ("you should", "don't", "don’t")
TRUTHY = {"1", "true", "yes"}

SYSTEM_PROMPT = (
    "You write a short career explanation for a 17-year-old in the UK. "
    "Use plain English and fewer than 120 words. Say careers are \"worth exploring\". "
    "Never use the phrases \"you should\" or \"don't\". "
    "Use only numbers that appear in the data you are given; never add or round numbers yourself. "
    "Copy each notice sentence word for word."
)

# Numbers written as words ("fifty-seven thousand", "double by twenty thirty") can't be checked against the
# response, so they send the text to the template. Bare "one" is left out: it is ordinary prose.
_NUMBER_WORDS = (
    "zero|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    "seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
    "hundred|thousand|million|billion|dozen|twice|double[sd]?|triple[sd]?|half|quarter"
)
_WORD_NUMBER = re.compile(r"\b(?:" + _NUMBER_WORDS + r")\b", re.IGNORECASE)

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


def _post(url: str, headers: dict[str, str], payload: dict[str, Any],
          timeout: tuple[float, float]) -> tuple[int, Any]:
    """Runs in a worker thread: (status code, message content, or None for a non-2xx)."""
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    status = resp.status_code
    return status, (resp.json()["choices"][0]["message"]["content"] if 200 <= status < 300 else None)


class LlmExplanation:
    """ExplanationWriter over an OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 3.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._clock = clock
        self._breaker_until = 0.0
        self._fallback = TemplateExplanation()

    def explain(self, rec: RecommendationOut) -> Explanation:
        try:
            if self._clock() >= self._breaker_until:
                text = self._complete(rec)
                if text:
                    failed = self._failed_check(text, rec)
                    if failed is None:
                        return Explanation(text=text, ai_written=True, cited_numbers=sorted(numbers_in(text)))
                    log.warning("LLM text rejected: %s", failed)
        except Exception as e:  # never raise: any failure means the template
            log.warning("LLM explanation failed: %s", type(e).__name__)
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
        url = f"{self.base_url}/chat/completions"
        deadline = self._clock() + self.timeout
        trip = False  # sticky: a timeout followed by a 5xx still opens the breaker
        for attempt in range(2):
            remaining = deadline - self._clock()
            if remaining <= 0 or (attempt == 1 and remaining < MIN_RETRY_SECONDS):
                break
            retry = False
            try:
                status, content = call_with_deadline(_post, remaining, url, headers, payload,
                                                     (remaining, remaining))
            except (DeadlineExceeded, requests.Timeout, requests.ConnectionError) as e:
                log.warning("LLM call failed: %s", type(e).__name__)
                retry = trip = True
            except Exception as e:  # bad JSON, unexpected shape: template, no retry
                log.warning("LLM call failed: %s", type(e).__name__)
            else:
                if 200 <= status < 300:
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                    log.warning("LLM call failed: empty response")
                else:
                    log.warning("LLM call failed: HTTP %s", status)
                    retry = status >= 500
                    trip = trip or status in (401, 403, 429)
            if not retry:
                break
        if trip:
            self._breaker_until = self._clock() + BREAKER_S
            log.warning("LLM calls paused for %.0f s", BREAKER_S)
        return None

    @staticmethod
    def _failed_check(text: str, rec: RecommendationOut) -> str | None:
        """Name of the first check the text fails, or None. Notices are verbatim, so they are exempt
        from the number and number-word checks (some contain digits)."""
        if any(n not in text for n in rec.notices):
            return "notice check"
        body = text
        for n in sorted(rec.notices, key=len, reverse=True):
            body = body.replace(n, " ")
        if numbers_in(body) - allowed_numbers(rec) or _WORD_NUMBER.search(body):
            return "number check"
        lowered = text.lower()
        if any(p in lowered for p in BANNED_PHRASES):
            return "wording check"
        return None


def writer_from_env(env: Mapping[str, str] | None = None) -> ExplanationWriter:
    """LlmExplanation only when LLM_ENABLED is truthy and base URL, key and model are all set."""
    env = os.environ if env is None else env
    enabled = env.get("LLM_ENABLED", "").strip().lower() in TRUTHY
    base, key, model = (env.get(k, "").strip() for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"))
    if enabled and base and key and model:
        return LlmExplanation(base, key, model)
    return TemplateExplanation()
