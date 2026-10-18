"""Guide tool use: read-only tools over the app's own data and the tool-calling loop, with a fake transport."""

import copy
import json
import sys
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

TOOL_REPLY = (
    "Software developer is worth exploring if you enjoy building things. Median pay was £56,914 a year for "
    "full-time employees in 2025 (get_role_stats: ONS ASHE 2025). At BlackRock, self-reported UK base pay for "
    "an Analyst ranges £43,000–£66,000 (get_employer: Glassdoor UK); ranges are not offers. "
    "Based on: ONS ASHE, Glassdoor UK."
)


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


@pytest.fixture()
def ctx():
    from api.main import _tool_context

    return _tool_context()


class _Response:
    def __init__(self, body: dict, status_code: int = 200):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _openai_env(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_BASE_URL", "http://model.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")


def _call(call_id: str, name: str, args) -> dict:
    arguments = args if isinstance(args, str) else json.dumps(args)
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def _tools_turn(*calls: dict) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": list(calls)}}]}


def _final(text: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _scripted_post(monkeypatch, bodies: list[dict]) -> list[dict]:
    """Returns the scripted bodies in order and records a deep copy of every payload sent."""
    calls: list[dict] = []
    queue = list(bodies)

    def post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "payload": copy.deepcopy(json)})
        return _Response(queue.pop(0))

    monkeypatch.setattr(requests, "post", post)
    return calls


def test_tools_execute_and_return_sourced_data(ctx):
    from api.guide_tools import run_tool

    stats, summary = run_tool(ctx, "get_role_stats", {"soc": "2134"})
    assert stats["title"] == "Software developer"
    assert "£56,914" in stats["metrics"]["pay"]["display"] and stats["metrics"]["pay"]["source"] == "ons_ashe_t14"
    assert stats["sources"] and all(source["name"] for source in stats["sources"])
    assert len(stats["hedges"]) == 3 and stats["crisis_checks"]
    assert summary.startswith("get_role_stats(2134): pay") and "3 hedges" in summary

    found, summary = run_tool(ctx, "search_jobs", {"query": "engineer", "limit": 3})
    assert 1 <= len(found["results"]) <= 3 and found["matched"] >= len(found["results"])
    assert all("engineer" in row["title"].lower() and row["soc"] for row in found["results"])
    assert any(source.get("coverage") == "UK (some indicators GB)" for source in found["sources"])
    assert summary.startswith("search_jobs(query=engineer)")
    critical, _ = run_tool(ctx, "search_jobs", {"demand": "critical", "min_pay": 40000, "limit": 8})
    assert critical["results"] and all(row["demand"] == "Critical" for row in critical["results"])

    compared, summary = run_tool(ctx, "compare_roles", {"socs": ["2134", "2135"]})
    assert [role["soc"] for role in compared["roles"]] == ["2134", "2135"]
    assert all(role["pay"] for role in compared["roles"])

    path, summary = run_tool(ctx, "get_career_path", {"soc": "2134"})
    assert {"routes", "courses", "skills", "grades_note", "first_step"} <= set(path)

    employer, summary = run_tool(ctx, "get_employer", {"name": "BlackRock"})
    assert employer["employer"] == "BlackRock" and employer["ways_in"] and employer["pay_works"]
    assert employer["career_ladder_uk"]["levels"][1]["level"] == "Analyst"
    assert employer["career_ladder_uk"]["source"]


def test_unknown_tool_and_bad_args_return_errors(ctx):
    from api.guide_tools import parse_args, run_tool

    assert "error" in run_tool(ctx, "delete_everything", {})[0]
    assert "error" in run_tool(ctx, "get_role_stats", {"soc": "abc"})[0]
    assert "error" in run_tool(ctx, "get_role_stats", {"soc": "0000"})[0]
    assert "error" in run_tool(ctx, "get_role_stats", None)[0]
    assert "error" in run_tool(ctx, "search_jobs", {"limit": "many"})[0]
    assert "error" in run_tool(ctx, "search_jobs", {"demand": "huge"})[0]
    assert "error" in run_tool(ctx, "compare_roles", {"socs": ["2134", "2135", "2136", "2137"]})[0]
    assert "error" in run_tool(ctx, "get_employer", {"name": "Acme"})[0]
    assert parse_args("not json") is None and parse_args("") == {} and parse_args({"soc": "2134"}) == {"soc": "2134"}


def test_two_round_tool_conversation_reports_tools_and_passes_number_check(client, monkeypatch):
    _openai_env(monkeypatch)
    calls = _scripted_post(
        monkeypatch,
        [
            _tools_turn(_call("c1", "get_role_stats", {"soc": "2134"})),
            _tools_turn(_call("c2", "get_employer", {"name": "BlackRock"})),
            _final(TOOL_REPLY),
        ],
    )
    answer = client.post("/api/guide", json={"soc": "2134", "message": "How does pay compare at BlackRock?"}).json()
    assert answer["mode"] == "llm_grounded" and answer["checks"] == "passed"
    assert answer["text"] == TOOL_REPLY.split(" Based on:")[0]
    assert [tool["name"] for tool in answer["tools_used"]] == ["get_role_stats", "get_employer"]
    assert answer["tools_used"][0]["args"] == {"soc": "2134"}
    assert answer["tools_used"][0]["summary"].startswith("get_role_stats(2134): pay")
    for field in ("links", "path", "profile_used", "compared", "based_on", "sources", "note"):
        assert field in answer
    assert len(calls) == 3
    first = calls[0]["payload"]
    assert first["tool_choice"] == "auto"
    assert {tool["function"]["name"] for tool in first["tools"]} == {
        "get_role_stats",
        "search_jobs",
        "compare_roles",
        "get_career_path",
        "get_employer",
    }
    system = first["messages"][0]["content"]
    assert "Pick the tools that fit the question" in system and "80-140 words" in system and "Evidence pack" in system
    third = calls[2]["payload"]["messages"]
    tool_messages = [m for m in third if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_messages] == ["c1", "c2"]
    assert "Glassdoor" in tool_messages[1]["content"]


def test_reply_with_a_number_from_no_tool_falls_back(client, monkeypatch):
    _openai_env(monkeypatch)
    _scripted_post(
        monkeypatch,
        [
            _tools_turn(_call("c1", "get_role_stats", {"soc": "2134"})),
            _final("Software developer pay is £99,999 a year. Based on: ONS ASHE."),
        ],
    )
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "prepared_demo" and answer["tools_used"] == []
    assert answer["checks"].startswith("fallback: number not in the evidence pack")


def test_unknown_tool_and_bad_args_inside_the_loop(client, monkeypatch):
    _openai_env(monkeypatch)
    calls = _scripted_post(
        monkeypatch,
        [
            _tools_turn(
                _call("c1", "delete_everything", {}),
                _call("c2", "get_role_stats", "not json"),
                _call("c3", "compare_roles", {"socs": "2134"}),
            ),
            _final(TOOL_REPLY.split(" At BlackRock")[0] + " Based on: ONS ASHE."),
        ],
    )
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "llm_grounded" and answer["checks"] == "passed"
    summaries = [tool["summary"] for tool in answer["tools_used"]]
    assert summaries[0] == "delete_everything: unknown tool"
    assert summaries[1] == "get_role_stats: bad arguments"
    assert summaries[2].startswith("compare_roles: error")
    sent = [m for m in calls[1]["payload"]["messages"] if m["role"] == "tool"]
    assert len(sent) == 3 and all("error" in json.loads(m["content"]) for m in sent)


def test_transport_error_mid_loop_falls_back_with_reason(client, monkeypatch):
    _openai_env(monkeypatch)
    bodies = [_tools_turn(_call("c1", "get_role_stats", {"soc": "2134"}))]

    def post(url, headers=None, json=None, timeout=None):
        if bodies:
            return _Response(bodies.pop(0))
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", post)
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "prepared_demo" and answer["checks"] == "fallback: ConnectionError"


def test_anthropic_tool_use_round(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    reply = TOOL_REPLY.split(" At BlackRock")[0] + " Based on: ONS ASHE."
    calls = _scripted_post(
        monkeypatch,
        [
            {"content": [{"type": "tool_use", "id": "t1", "name": "get_role_stats", "input": {"soc": "2134"}}]},
            {"content": [{"type": "text", "text": reply}]},
        ],
    )
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "llm_grounded" and answer["tools_used"][0]["name"] == "get_role_stats"
    assert calls[0]["payload"]["tools"][0]["input_schema"]
    follow_up = calls[1]["payload"]["messages"][-1]
    assert follow_up["role"] == "user" and follow_up["content"][0]["tool_use_id"] == "t1"


def test_quota_error_retries_once_with_the_second_key_and_remembers(client, monkeypatch):
    from api import guide_llm

    monkeypatch.setattr(guide_llm, "_EXHAUSTED", set())
    _openai_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY_2", "second-key")
    reply = TOOL_REPLY.split(" At BlackRock")[0] + " Based on: ONS ASHE."
    seen: list[str] = []

    def post(url, headers=None, json=None, timeout=None):
        seen.append(headers["Authorization"])
        if headers["Authorization"] == "Bearer test-key":
            return _Response({"error": "quota"}, status_code=429)
        return _Response(_final(reply))

    monkeypatch.setattr(requests, "post", post)
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "llm_grounded" and seen == ["Bearer test-key", "Bearer second-key"]
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What about jobs?"}).json()
    assert answer["mode"] == "llm_grounded"
    assert seen[2:] == ["Bearer second-key"]  # the exhausted first key is skipped for the rest of the process


def test_quota_error_on_the_only_key_falls_back(client, monkeypatch):
    from api import guide_llm

    monkeypatch.setattr(guide_llm, "_EXHAUSTED", set())
    _openai_env(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Response({}, status_code=429))
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "prepared_demo" and answer["checks"] == "fallback: HTTP 429"


def test_accepted_reply_is_cached_and_replayed_without_a_request(client, monkeypatch):
    _openai_env(monkeypatch)
    tools = _tools_turn(_call("c1", "get_role_stats", {"soc": "2134"}), _call("c2", "get_employer", {}))
    calls = _scripted_post(monkeypatch, [tools, _final(TOOL_REPLY)])
    request = {"soc": "2134", "message": "How does pay compare at BlackRock?", "profile": {"tags": ["maths"]}}
    first = client.post("/api/guide", json=request).json()
    assert first["mode"] == "llm_grounded" and first["cached"] is False and len(calls) == 2
    second = client.post("/api/guide", json=request).json()
    assert len(calls) == 2, "a cache hit must not call the model"
    assert second["cached"] is True and second["text"] == first["text"] and second["tools_used"] == first["tools_used"]
    assert second["links"] == first["links"] and second["mode"] == "llm_grounded"
    other = client.post("/api/guide", json={**request, "profile": {"tags": ["art"]}})
    assert other.status_code == 200 and other.json()["cached"] is False  # a different profile is a different key


def test_no_model_configured_keeps_prepared_behaviour(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Tell me about pay"}).json()
    assert answer["mode"] == "prepared_demo" and answer["checks"] == "fallback: no model configured"
    assert answer["tools_used"] == [] and "£56,914" in answer["text"]
