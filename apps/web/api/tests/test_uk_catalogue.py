"""The added plumbing profile must retain its own evidence and honest coverage."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_plumber_is_the_only_extra_career_and_keeps_canonical_evidence():
    from api.main import app
    from pathfinder_ml import ML

    client = TestClient(app)
    data = client.get("/api/bootstrap").json()
    expected = {occupation["soc2020"] for occupation in ML().occupations(demo_only=True)} | {"5315"}
    assert {career["soc"] for career in data["careers"]} == expected
    plumber = next(career for career in data["careers"] if career["soc"] == "5315")
    assert plumber["title"] == "Plumber"
    assert plumber["metrics"] == ML().occupation("5315")["metrics"]
    assert plumber["history"] == ML().history("5315")
    assert plumber["metrics"]["pay_median"]["value"] == 37881
    assert plumber["family"] == "explore"


def test_plumber_route_and_guide_do_not_borrow_misclassified_prototype_content():
    from api.main import app

    client = TestClient(app)
    route = client.get("/api/path/5315")
    assert route.status_code == 404
    assert "not available" in route.json()["detail"]
    pay = client.post("/api/guide", json={"soc": "5315", "message": "What is the salary?"}).json()
    assert "37,881" in pay["text"]
    skills = client.post("/api/guide", json={"soc": "5315", "message": "What is the study route?"})
    assert skills.status_code == 200
    assert "not been added" in skills.json()["text"]
    assert any(source.get("url", "").endswith("/plumber") for source in skills.json()["sources"])


def test_uncalibrated_plumber_profile_is_catalogue_only():
    from api.main import app

    client = TestClient(app)
    result = client.post(
        "/api/matches",
        json={
            "tags": ["fixing_hands_on"],
            "weights": {"pay": 15, "interest": 70, "need": 15},
        },
    ).json()
    assert len(result["results"]) == 20
    assert all(career["soc"] != "5315" for career in result["results"])
    discovery = client.post(
        "/api/discovery",
        json={
            "mode": "explore",
            "answers": {"interests": "Fixing things and working with tools"},
        },
    ).json()
    assert len(discovery["results"]) == 3
    assert all(career["soc"] != "5315" for career in discovery["results"])
