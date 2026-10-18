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

import hashlib
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

from . import guide_tools
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
    fallback_headers: dict[str, str] | None = field(default=None, repr=False)  # LLM_API_KEY_2, used on quota errors


def config_from_env(env: Mapping[str, str] | None = None) -> ModelConfig | None:
    """The configured model, or None (prepared replies only). The key is read here and kept out of logs."""
    env = os.environ if env is None else env

    def get(name: str) -> str:
        return (env.get(name) or "").strip()

    base, key, model = get("LLM_BASE_URL"), get("LLM_API_KEY"), get("LLM_MODEL")
    if get("LLM_ENABLED").lower() in TRUTHY and base and key and model:
        second = get("LLM_API_KEY_2")
        fallback = {"Authorization": f"Bearer {second}"} if second and second != key else None
        url = base.rstrip("/") + "/chat/completions"
        return ModelConfig("openai", url, model, {"Authorization": f"Bearer {key}"}, fallback)
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


# --- Tool use: the model fetches Aventier's own data itself (guide_tools), then answers. ---

TOOL_DEADLINE_S = 25.0
MAX_TOOL_ROUNDS = 2  # each round is one model request (free-tier quotas): 2 tool rounds plus the final answer
MAX_CALLS_PER_ROUND = 6
QUOTA_STATUSES = (429, 403)
_EXHAUSTED: set[str] = set()  # fingerprints of keys that hit a quota error; kept for the life of the process
TOOL_MAX_TOKENS = 1500  # OpenAI-compatible path: room for Gemini models that count thinking tokens as output
TOOLS_PROMPT = (
    "\n\nTools: you can call read-only tools that return Aventier's own data with sources: get_role_stats, "
    "search_jobs, compare_roles, get_career_path and get_employer (BlackRock only). Use the tools to fetch the "
    "facts before you answer, for this role or any role the student mentions. Every number must come from the "
    "evidence pack or a tool result, copied as written. Cite which tool and source each figure came from, e.g. "
    "\"(get_role_stats: ONS ASHE 2025)\". When the student's quiz preferences are given, tie the advice to them. "
    "Describe history, not forecasts. Never write \"you should\". Keep the reply under 180 words."
)


def _tool_system(system: str) -> str:
    head, sep, rest = system.partition("\n\nEvidence pack:\n")
    head = head.replace(
        "Use ONLY the facts in the evidence pack below.",
        "Use ONLY the facts in the evidence pack below and in tool results.",
    )
    head = head.replace("under 160 words", "under 180 words")
    return head + TOOLS_PROMPT + sep.replace("Evidence pack:", "Evidence pack (headline metrics; tools have the rest):") + rest


def _fingerprint(headers: dict[str, str]) -> str:
    return hashlib.sha256(_compact(sorted(headers.items())).encode()).hexdigest()


def _send(config: ModelConfig, payload: dict[str, Any], deadline: float) -> tuple[int, Any]:
    """One model request. On a quota error (429/403) the key is marked exhausted and the same request is
    retried once with the other key (LLM_API_KEY_2); keys not yet exhausted are tried first."""
    keys = [config.headers] + ([config.fallback_headers] if config.fallback_headers else [])
    keys.sort(key=lambda headers: _fingerprint(headers) in _EXHAUSTED)  # stable: fresh keys first
    status, body = 0, None
    for headers in keys[:2]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DeadlineExceeded()
        status, body = call_with_deadline(_post, remaining, config.url, headers, payload, remaining)
        if status not in QUOTA_STATUSES:
            return status, body
        _EXHAUSTED.add(_fingerprint(headers))
        log.warning("guide model key hit a quota error (HTTP %s); trying the other key if set", status)
    return status, body


SLIM_METRIC_KEYS = ("value", "display", "source", "as_of", "caveats")


def slim_pack(pack: dict) -> dict:
    """The headline metrics only; with tools on, the model fetches hedges, demand and the rest itself."""
    metrics = {
        key: {k: entry.get(k) for k in SLIM_METRIC_KEYS}
        for key, entry in (pack.get("metrics") or {}).items()
        if entry.get("value") is not None
    }
    return {"soc": pack.get("soc"), "title": pack.get("title"), "metrics": metrics}


def build_tool_request(
    config: ModelConfig, pack: dict, message: str, history: list[Any], *, compared: list[dict] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """A compact grounded request (headline metrics, not the whole pack) plus tool definitions and instructions."""
    slim_compared = [slim_pack(other) for other in compared or []]
    payload = build_request(config, slim_pack(pack), message, history, compared=slim_compared, **kwargs)
    if config.provider == "anthropic":
        payload["system"] = _tool_system(payload["system"])
        payload["tools"] = guide_tools.anthropic_tools()
        return payload
    payload["messages"][0]["content"] = _tool_system(payload["messages"][0]["content"])
    payload["max_tokens"] = TOOL_MAX_TOKENS
    payload["tools"] = guide_tools.openai_tools()
    payload["tool_choice"] = "auto"
    return payload


def _tool_calls(provider: str, body: Any) -> tuple[list[dict], dict]:
    """([{id, name, args}], the assistant message to echo back). Raises on an unexpected shape."""
    if provider == "anthropic":
        blocks = body["content"]
        calls = [{"id": b["id"], "name": b.get("name"), "args": b.get("input")} for b in blocks if b.get("type") == "tool_use"]
        return calls, {"role": "assistant", "content": blocks}
    message = body["choices"][0]["message"]
    raw_calls = message.get("tool_calls") or []
    calls = [
        {"id": c.get("id"), "name": (c.get("function") or {}).get("name"), "args": (c.get("function") or {}).get("arguments")}
        for c in raw_calls
    ]
    return calls, {"role": "assistant", "content": message.get("content") or "", "tool_calls": raw_calls}


def tool_reply(
    config: ModelConfig,
    pack: dict,
    message: str,
    history: list[Any],
    ctx: guide_tools.ToolContext,
    *,
    preferences: dict | None = None,
    compared: list[dict] | None = None,
    link_labels: list[str] | None = None,
    path: dict | None = None,
) -> tuple[str | None, str, list[dict]]:
    """(accepted reply or None, check result, tools used). Never raises.

    Up to MAX_TOOL_ROUNDS rounds of tool calls, then a final answer, all within TOOL_DEADLINE_S. The number
    check allows every number in the pack, the compared packs, the preferences, the path and every tool result.
    On any fallback the tools list is empty: the prepared reply did not use them."""
    payload = build_tool_request(
        config, pack, message, history, preferences=preferences, compared=compared, link_labels=link_labels, path=path
    )
    allowed = set(pack.get("allowed_numbers", [])) | allowed_numbers(
        {"compared": compared or [], "preferences": preferences or {}, "path": path or {}}
    )
    used: list[dict] = []
    deadline = time.monotonic() + TOOL_DEADLINE_S
    text = ""
    for round_no in range(MAX_TOOL_ROUNDS + 1):
        if round_no == MAX_TOOL_ROUNDS:  # last round: answer with what has been fetched
            payload["tool_choice"] = {"type": "none"} if config.provider == "anthropic" else "none"
        try:
            status, body = _send(config, payload, deadline)
        except (DeadlineExceeded, requests.Timeout) as error:
            return None, "fallback: " + ("timeout" if isinstance(error, requests.Timeout) else "deadline exceeded"), []
        except Exception as error:  # noqa: BLE001  (any transport failure means the prepared reply)
            return None, f"fallback: {type(error).__name__}", []
        if not 200 <= status < 300:
            return None, f"fallback: HTTP {status}", []
        try:
            calls, echo = _tool_calls(config.provider, body)
            if not calls:
                text = _reply_text(config.provider, body)
                break
        except (KeyError, IndexError, TypeError, AttributeError):
            return None, "fallback: unexpected response shape", []
        if round_no == MAX_TOOL_ROUNDS:
            return None, "fallback: still calling tools after the last round", []
        results = []
        for call in calls[:MAX_CALLS_PER_ROUND]:
            args = guide_tools.parse_args(call["args"])
            result, summary = guide_tools.run_tool(ctx, call["name"], args)
            used.append({"name": str(call["name"]), "args": args if isinstance(args, dict) else None, "summary": summary})
            allowed |= allowed_numbers(result)
            results.append((call["id"], result))
        if config.provider == "anthropic":
            content = [{"type": "tool_result", "tool_use_id": cid, "content": _compact(r)} for cid, r in results]
            payload["messages"] += [echo, {"role": "user", "content": content}]
        else:
            payload["messages"] += [echo] + [{"role": "tool", "tool_call_id": cid, "content": _compact(r)} for cid, r in results]
    failed = failed_check(text, allowed)
    if failed:
        return None, f"fallback: {failed}", []
    return text, "passed", used
