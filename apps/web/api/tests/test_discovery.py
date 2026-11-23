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


@pytest.mark.parametrize(
    ("interests", "tag"),
    [("I enjoy maths", "maths"), ("I enjoy drawing", "art_drawing"), ("I enjoy explaining", "teaching_explaining")],
)
def test_stem_keywords_match_positive_activities_without_counting_salary_priorities(client, interests, tag):
    response = client.post(
        "/api/discovery",
        json={"mode": "explore", "answers": {"interests": interests, "values": "Money and business pay matter"}},
    )
    assert response.status_code == 200
    tags = response.json()["tags"]
    assert tag in tags
    assert "money_business" not in tags


def test_negated_stem_keyword_does_not_reenter_through_the_matcher(client):
    response = client.post(
        "/api/discovery",
        json={"mode": "explore", "answers": {"interests": "I dislike drawing, but enjoy maths"}},
    )
    assert response.status_code == 200
    assert "maths" in response.json()["tags"]
    assert "art_drawing" not in response.json()["tags"]


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


def test_reference_is_distinct_from_an_exact_target_for_related_careers(client):
    doctor = client.post("/api/discovery", json={"mode": "known", "answers": {"direction": "doctor"}}).json()
    assert doctor["target_soc"] is None
    assert doctor["reference_soc"] == doctor["results"][0]["soc"] == "2254"
    civil = client.post("/api/discovery", json={"mode": "known", "answers": {"direction": "civil engineer"}}).json()
    assert civil["reference_soc"] == civil["target_soc"] == "2121"
    explore = client.post("/api/discovery", json={"mode": "explore", "answers": {"subjects": "maths"}}).json()
    assert explore["reference_soc"] is None


def test_architectural_technologist_uses_disclosed_source_group_reference(client):
    data = client.post(
        "/api/discovery",
        json={
            "mode": "known",
            "answers": {
                "direction": "architectural technologist",
            },
        },
    ).json()
    assert data["target_soc"] is None
    assert data["reference_soc"] == "2452"
    assert any("occupation group" in notice.lower() for notice in data["notices"])


@pytest.mark.parametrize("value", ["Long-term demand", "long term demand", "job security"])
def test_demand_priority_chip_increases_need_weight(client, value):
    data = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {
                "subjects": "maths",
                "values": value,
            },
        },
    ).json()
    assert data["weights"] == {"pay": 15, "interest": 55, "need": 30}


def test_example_profile_answers_work_without_keys_or_network(client):
    """The guided demo's sample answers (Amira) must produce matches from the bundled evidence alone."""
    answers = {
        "direction": "Architect",
        "interests": "Making or designing something; Solving a tricky problem",
        "subjects": "Maths; Art and design",
        "values": "Long-term demand; Making a useful impact",
        "skills": "Maths and data; Drawing or design",
    }
    response = client.post("/api/discovery", json={"mode": "known", "answers": answers})
    assert response.status_code == 200
    data = response.json()
    assert data["target_soc"] and len(data["results"]) >= 3
    assert all(result["metrics"]["pay_median"]["as_of"] for result in data["results"])
