"""Conversational discovery exercises actual supplied affinities and evidence."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


def test_explore_answers_create_three_distinct_grounded_options(client):
    response = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {
                "interests": "I enjoy coding games and solving puzzles",
                "subjects": "Maths and computing",
                "skills": "I like explaining ideas to a team",
                "values": "I want interesting work",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == len({career["soc"] for career in data["results"]}) == 3
    assert data["target_soc"] is None
    assert "computers_coding" in data["tags"]
    assert data["profile_summary"]
    assert data["weights"] == {"pay": 15, "interest": 70, "need": 15}
    from pathfinder_ml import ML

    for career in data["results"]:
        assert career["metrics"] == ML().occupation(career["soc"])["metrics"]
        assert career["history"] == ML().history(career["soc"])
        assert career["fit_status"] == ML()._load("fit")["status"]


def test_known_career_is_kept_as_an_explicit_reference(client):
    response = client.post(
        "/api/discovery",
        json={
            "mode": "known",
            "answers": {
                "direction": "I want to be a software engineer",
                "subjects": "English and art",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["target_soc"] == "2134"
    assert data["results"][0]["soc"] == "2134"
    assert len(data["results"]) == 3
    assert any("reference" in notice.lower() for notice in data["notices"])


def test_known_sparse_direction_seeds_actual_career_affinities(client):
    response = client.post("/api/discovery", json={"mode": "known", "answers": {"direction": "actuary"}})
    assert response.status_code == 200
    assert response.json()["target_soc"] == "2433"
    assert response.json()["tags"]


def test_unsupported_doctor_is_labelled_related_healthcare_not_exact(client):
    response = client.post("/api/discovery", json={"mode": "known", "answers": {"direction": "doctor"}})
    assert response.status_code == 200
    data = response.json()
    assert data["target_soc"] is None
    assert data["results"][0]["soc"] == "2254"
    assert any("not an exact match" in notice.lower() for notice in data["notices"])


def test_subject_synonyms_and_stated_values_are_applied_transparently(client):
    data = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {
                "subjects": "CS and statistics",
                "values": "Financial security and a high salary are important",
            },
        },
    ).json()
    assert "computers_coding" in data["tags"]
    assert "maths" in data["tags"]
    assert data["weights"]["pay"] > 15
    assert any("weight" in notice.lower() for notice in data["notices"])


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "explore", "answers": {}},
        {"mode": "explore", "answers": {"interests": "not sure yet"}},
        {"mode": "known", "answers": {"direction": "astronaut"}},
        {"mode": "unknown", "answers": {"subjects": "maths"}},
        {"mode": "explore", "answers": {"subjects": 123}},
    ],
)
def test_empty_unsupported_and_invalid_input_is_actionable(client, payload):
    response = client.post("/api/discovery", json=payload)
    assert response.status_code == 422
    if payload["mode"] in ("known", "explore") and not isinstance(payload["answers"].get("subjects"), int):
        assert "subject or activity" in response.json()["detail"].lower()


def test_explicit_dislike_is_not_treated_as_an_interest(client):
    response = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {
                "interests": "I dislike coding, but enjoy helping people",
            },
        },
    )
    assert response.status_code == 200
    assert "helping_people" in response.json()["tags"]
    assert "computers_coding" not in response.json()["tags"]
    negative_only = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {
                "interests": "I don't like programming",
            },
        },
    )
    assert negative_only.status_code == 422


def test_known_civil_engineer_resolves_exact_reference(client):
    response = client.post(
        "/api/discovery",
        json={
            "mode": "known",
            "answers": {
                "direction": "I want to be a civil engineer",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["target_soc"] == "2121"
    assert response.json()["results"][0]["soc"] == "2121"
