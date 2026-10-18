"""The guide with the quiz profile, API-built links and the career path; no network or credentials."""

import sys
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PROFILE = {
    "tags": ["maths", "computers_coding"],
    "weights": {"pay": 30, "interest": 45, "need": 25},
    "selected": ["2134", "2451", "3544"],
    "free_text": "I like building things that people use.",
}
PATH_REPLY = (
    "Software developer is worth exploring given your interest in computers and coding. The published median pay is "
    "£56,914 a year for full-time employees (2025). The 2025 figure is an ONS provisional estimate and may be revised. "
    "Routes: University, or Apprenticeship and college. Grades vary by course and nation; see the course pages. "
    "Based on: ONS ASHE."
)


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


class _Response:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _model_env(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_BASE_URL", "http://model.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")


def _fake_post(monkeypatch, reply: str) -> list[dict]:
    calls: list[dict] = []

    def post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "payload": json})
        return _Response(200, {"choices": [{"message": {"content": reply}}]})

    monkeypatch.setattr(requests, "post", post)
    return calls


def test_health_and_bootstrap_say_the_guide_accepts_a_profile(client):
    assert client.get("/api/health").json()["guide_accepts_profile"] is True
    assert client.get("/api/bootstrap").json()["data_status"]["guide_accepts_profile"] is True


def test_profile_is_validated_and_reflected_in_the_prompt_with_compared_roles(client, monkeypatch):
    _model_env(monkeypatch)
    calls = _fake_post(monkeypatch, PATH_REPLY)
    answer = client.post(
        "/api/guide", json={"soc": "2134", "message": "What is the path into this career?", "profile": PROFILE}
    ).json()
    assert (
        answer["mode"] == "llm_grounded" and answer["checks"] == "passed" and answer["text"] == PATH_REPLY.split(" Based on:")[0]
    )
    assert answer["profile_used"] is True and answer["compared"] == ["2451", "3544"]
    system = calls[0]["payload"]["messages"][0]["content"]
    assert "Student's preferences" in system
    assert "cares most about interest, then pay, then UK need" in system
    assert "Maths and numbers" in system and "Computers and coding" in system
    assert "Architect (2451)" in system and "Data analyst (3544)" in system
    assert "I like building things that people use." in system
    assert "Other roles the student selected" in system and "never claim they predict" in system
    assert "cite them by label only" in system and "Architect in Aventier" in system
    assert "The student asked for a career path" in system and "grades_note" in system
    assert "allowed_numbers" not in system
    # A bad profile is rejected, and unknown fields stay forbidden.
    for profile in ({"tags": ["x"], "bogus": 1}, {"selected": ["21345"]}, {"weights": {"pay": 101}}):
        assert client.post("/api/guide", json={"soc": "2134", "message": "hi", "profile": profile}).status_code == 422


def test_path_question_without_a_model_returns_the_structured_path_and_links(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "How do I become one?", "profile": PROFILE}).json()
    assert answer["mode"] == "prepared_demo" and answer["profile_used"] is True
    path = answer["path"]
    assert set(path) == {"routes", "courses", "skills", "grades_note", "first_step"}
    assert path["routes"][0] == {
        "label": "University",
        "summary": "Study a degree, and use it to build skills, contacts and evidence.",
    }
    assert any(route["label"].startswith("Graduate Apprenticeship") for route in path["routes"])
    assert path["courses"][0]["label"] == "Computer science (BSc)"
    assert any(course.get("href", "").startswith("https://") for course in path["courses"])
    assert path["skills"][0] == "use an application-specific interface" and len(path["skills"]) == 8
    assert "holds no entry requirements" in path["grades_note"] and "vary by course" in path["grades_note"]
    assert path["first_step"]
    # The prepared text walks the same structure and names the student's tags and selected roles.
    assert "Maths and numbers" in answer["text"] and "Architect (2451)" in answer["text"]
    assert "you care most about interest, then pay, then UK need" in answer["text"]
    assert "University" in answer["text"] and "About grades:" in answer["text"] and "First step this month:" in answer["text"]
    hrefs = [link["href"] for link in answer["links"]]
    assert hrefs[:3] == ["#/guides/2134", "#/guides/2451", "#/guides/3544"]
    assert answer["links"][1]["label"] == "Architect in Aventier"
    pack = client.get("/api/careers/2134/evidence-pack").json()
    source_urls = [source["url"] for source in pack["sources"] if source.get("url")]
    assert source_urls and all(url in hrefs for url in source_urls)
    assert len(hrefs) == len(set(hrefs))
    assert pack["skills"] == path["skills"]


def test_non_path_question_has_links_but_no_path_and_a_preference_sentence(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the pay?", "profile": PROFILE}).json()
    assert answer["path"] is None and answer["links"][0]["href"] == "#/guides/2134"
    assert "56,914" in answer["text"] and "not your outcome" in answer["text"]
    plain = client.post("/api/guide", json={"soc": "2134", "message": "What is the pay?"}).json()
    assert plain["profile_used"] is False and plain["compared"] == [] and plain["path"] is None
    assert "not your outcome" not in plain["text"] and plain["links"][0]["href"] == "#/guides/2134"


def test_role_without_a_curated_pathway_gets_an_honest_path(client):
    answer = client.post("/api/guide", json={"soc": "5315", "message": "what should I study?"}).json()
    path = answer["path"]
    assert path["routes"] == [] and path["courses"] == []
    assert path["skills"] and "No curated pathway example" in path["first_step"]
    assert "holds no entry requirements" in path["grades_note"]


def test_number_check_still_rejects_a_number_outside_every_pack(client, monkeypatch):
    _model_env(monkeypatch)
    _fake_post(monkeypatch, "Architect pay is £99,999 a year. Based on: ONS ASHE.")
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Plan my route", "profile": PROFILE}).json()
    assert answer["mode"] == "prepared_demo" and answer["checks"].startswith("fallback: number not in the evidence pack")
    assert answer["path"] is not None and answer["links"]
    # A compared role's own figure passes, because every included pack is allowed.
    architect = client.get("/api/careers/2451/evidence-pack").json()["metrics"]["pay"]["value"]
    _fake_post(monkeypatch, f"Architect pay is £{architect:,.0f} a year. Based on: ONS ASHE.")
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Compare them", "profile": PROFILE}).json()
    assert answer["checks"] == "passed"
