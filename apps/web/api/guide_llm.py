"""Model-written guide replies grounded in a role's evidence pack, with hard checks.

The model sees only the evidence pack (without `allowed_numbers`), the last few turns and the
question. Its reply is accepted only if every number in it appears in the pack's `allowed_numbers`,
it avoids the banned phrases, is not empty and is under MAX_CHARS. Any failure, timeout, HTTP error
or exception means the caller falls back to the prepared reply; the reason is returned in the
response. Logs carry only that reason, never a key, URL, prompt or reply text.

Configuration (same names as the LLM explanation writer): `LLM_ENABLED`, `LLM_BASE_URL`,
`LLM_API_KEY`, `LLM_MODEL` for an OpenAI-compatible chat-completions endpoint; or
`ANTHROPIC_API_KEY` (with `LLM_BASE_URL` empty) for the Anthropic Messages API.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import requests

from avenir_adapters._deadline import DeadlineExceeded, call_with_deadline
from avenir_adapters.llm.writer import TRUTHY, numbers_in

from .evidence_pack import allowed_numbers

log = logging.getLogger(__name__)

TIMEOUT_S = 20.0
MAX_TOKENS = 600
MAX_CHARS = 1200
HISTORY_TURNS = 6
BANNED_PHRASES = ("you should", "don't", "don’t", "guarantee", "will earn", "probability")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"
PROMPT_EXCLUDED_KEYS = ("allowed_numbers", "based_on")

SYSTEM_PROMPT = (
    "You are a careers guide for a 17-year-old in the UK. Use ONLY the facts in the evidence pack below. "
    "Every number you quote must appear in the pack, written the same way (same digits, commas and decimal "
    "places); never add, round or convert numbers yourself. When you use a figure, copy its caveat sentences "
    "word for word. History is not a forecast: describe what happened, never what will happen. Never give "
    "probabilities of job loss, graduate or starting salaries, or the words \"you should\" or \"don't\"; say "
    "careers are \"worth exploring\". If the pack has no answer, say so plainly. Write in plain English, under "
    "160 words. End with one line starting \"Based on:\" that names the sources you used.\n\nEvidence pack:\n"
)
COMPARED_PROMPT = "\n\nOther roles the student selected (metrics and hedges only), so you can compare:\n"
PREFERENCES_PROMPT = (
    "\n\nStudent's preferences (from the quiz, or stated in chat):\n{words}\n"
    "Tie every opinion to these preferences AND to the figures in the packs. When a preference and the figures "
    "pull in different directions, say so plainly. The figures describe what happened to employees in the past; "
    "never claim they predict this student's outcome."
)
LINKS_PROMPT = (
    "\n\nThe app shows these links under your reply; cite them by label only and never write a URL: {labels}"
)
PATH_PROMPT = (
    "\n\nThe student asked for a career path. Walk through it in prose: the routes, the courses, the skills to "
    "build, and what can be said about grades, using only the path data below and the packs' numbers. The app "
    "holds no entry requirements: say grades vary by course and nation and point to the course pages.\nPath data:\n"
)


def _compact(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class ModelConfig:
    provider: str  # "openai" or "anthropic"
    url: str
    model: str
    headers: dict[str, str] = field(repr=False)  # never printed: carries the key


def config_from_env(env: Mapping[str, str] | None = None) -> ModelConfig | None:
    """The configured model, or None (prepared replies only). The key is read here and kept out of logs."""
    env = os.environ if env is None else env

    def get(name: str) -> str:
        return (env.get(name) or "").strip()

    base, key, model = get("LLM_BASE_URL"), get("LLM_API_KEY"), get("LLM_MODEL")
    if get("LLM_ENABLED").lower() in TRUTHY and base and key and model:
        return ModelConfig("openai", base.rstrip("/") + "/chat/completions", model, {"Authorization": f"Bearer {key}"})
    anthropic_key = get("ANTHROPIC_API_KEY")
    if anthropic_key and not base:
        headers = {"x-api-key": anthropic_key, "anthropic-version": ANTHROPIC_VERSION}
        return ModelConfig("anthropic", ANTHROPIC_URL, model or DEFAULT_ANTHROPIC_MODEL, headers)
    return None


def _turns(history: list[Any], message: str) -> list[dict[str, str]]:
    """The last few turns plus the question, as alternating user/assistant messages starting with the user."""
    turns = [{"role": t.role, "content": t.content} for t in history[-HISTORY_TURNS:]]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    merged: list[dict[str, str]] = []
    for turn in turns + [{"role": "user", "content": message}]:
        if merged and merged[-1]["role"] == turn["role"]:
            merged[-1]["content"] += "\n" + turn["content"]
        else:
            merged.append(dict(turn))
    return merged


def build_request(
    config: ModelConfig,
    pack: dict,
    message: str,
    history: list[Any],
    *,
    preferences: dict | None = None,
    compared: list[dict] | None = None,
    link_labels: list[str] | None = None,
    path: dict | None = None,
) -> dict[str, Any]:
    prompt_pack = {k: v for k, v in pack.items() if k not in PROMPT_EXCLUDED_KEYS}
    system = SYSTEM_PROMPT + _compact(prompt_pack)
    if compared:
        system += COMPARED_PROMPT + _compact(compared)
    if preferences:
        system += PREFERENCES_PROMPT.format(words=_compact(preferences))
    if link_labels:
        system += LINKS_PROMPT.format(labels="; ".join(link_labels))
    if path:
        system += PATH_PROMPT + _compact(path)
    turns = _turns(history, message)
    if config.provider == "anthropic":
        return {"model": config.model, "max_tokens": MAX_TOKENS, "system": system, "messages": turns}
    return {
        "model": config.model,
        "messages": [{"role": "system", "content": system}, *turns],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
    }


def _post(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> tuple[int, Any]:
    """Runs in a worker thread: (status code, parsed JSON body or None for a non-2xx)."""
    resp = requests.post(url, headers=headers, json=payload, timeout=(timeout, timeout))
    return resp.status_code, (resp.json() if 200 <= resp.status_code < 300 else None)


def _reply_text(provider: str, body: Any) -> str:
    if provider == "anthropic":
        return "".join(block.get("text", "") for block in body["content"] if block.get("type", "text") == "text").strip()
    return str(body["choices"][0]["message"]["content"]).strip()


def failed_check(text: str, allowed: set[str]) -> str | None:
    """Name of the first hard check the reply fails, or None when it passes."""
    if not text or not text.strip():
        return "empty reply"
    if len(text) > MAX_CHARS:
        return f"reply over {MAX_CHARS:,} characters"
    stray = sorted(numbers_in(text) - allowed)
    if stray:
        return "number not in the evidence pack: " + ", ".join(stray[:5])
    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            return f"banned phrase: {phrase}"
    return None


def grounded_reply(
    config: ModelConfig,
    pack: dict,
    message: str,
    history: list[Any],
    *,
    preferences: dict | None = None,
    compared: list[dict] | None = None,
    link_labels: list[str] | None = None,
    path: dict | None = None,
) -> tuple[str | None, str]:
    """(accepted reply text or None, check result: "passed" or "fallback: <reason>"). Never raises.
    The number check allows every number in the role's pack, the compared packs, the preferences and the path."""
    payload = build_request(
        config, pack, message, history, preferences=preferences, compared=compared, link_labels=link_labels, path=path
    )
    allowed = set(pack.get("allowed_numbers", [])) | allowed_numbers(
        {"compared": compared or [], "preferences": preferences or {}, "path": path or {}}
    )
    deadline = time.monotonic() + TIMEOUT_S
    try:
        remaining = max(deadline - time.monotonic(), 0.1)
        status, body = call_with_deadline(_post, remaining, config.url, config.headers, payload, remaining)
    except (DeadlineExceeded, requests.Timeout) as error:
        return None, "fallback: " + ("timeout" if isinstance(error, requests.Timeout) else "deadline exceeded")
    except Exception as error:  # noqa: BLE001  (any transport or parsing failure means the prepared reply)
        return None, f"fallback: {type(error).__name__}"
    if not 200 <= status < 300:
        return None, f"fallback: HTTP {status}"
    try:
        text = _reply_text(config.provider, body)
    except (KeyError, IndexError, TypeError, AttributeError):
        return None, "fallback: unexpected response shape"
    failed = failed_check(text, allowed)
    if failed:
        return None, f"fallback: {failed}"
    return text, "passed"
