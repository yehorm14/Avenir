"""Exercise the real API with actual ML artefacts, without network or credentials."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


def test_bootstrap_passes_through_actual_arsenii_metrics_and_history(client):
    from pathfinder_ml import ML

    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    data = response.json()
    assert len(data["careers"]) == 20
    software = next(c for c in data["careers"] if c["soc"] == "2134")
    assert software["metrics"] == ML().occupation("2134")["metrics"]
    assert software["history"] == ML().history("2134")
    assert software["metrics"]["pay_median"]["value"] == 56914
    assert data["data_status"]["fit"] == "mock"
    assert set(data["sources"]) == set(ML().sources())


def test_match_endpoint_validates_profile_and_returns_every_career(client):
    unknown = client.post("/api/matches", json={"tags": ["not-real"], "weights": {"pay": 1, "interest": 1, "need": 1}})
    assert unknown.status_code == 422
    response = client.post("/api/matches", json={"tags": ["computers_coding"], "weights": {"pay": 0, "interest": 100, "need": 0}})
    assert response.status_code == 200
    result = response.json()
    assert len(result["results"]) == 20
    assert result["results"][0]["soc"] == "2134"
    assert result["results"][0]["fit"] == 95
    assert result["fit_status"] == "mock"
    assert client.post("/api/matches", json={"tags": [], "weights": {"pay": -1}}).status_code == 422


def test_all_twenty_careers_have_paths_without_max_mock_earnings(client):
    for career in client.get("/api/bootstrap").json()["careers"]:
        response = client.get(f"/api/path/{career['soc']}?nation=Scotland")
        assert response.status_code == 200, career["soc"]
        plan = response.json()
        assert plan["soc"] == career["soc"]
        assert plan["title"] == career["title"]
        assert plan["nation"] == "Scotland"
        assert plan["hard_skills"]
        assert all(d["median_earnings_15m"] is None for d in plan["degrees"])
        assert plan["demo_note"]
    assert client.get("/api/path/9999").status_code == 404


def test_demo_guide_is_grounded_and_declines_unrelated_requests(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "What is the salary and inflation?"}).json()
    assert "56,914" in answer["text"]
    assert answer["mode"] == "prepared_demo"
    assert answer["ai_written"] is False
    assert answer["sources"]
    ai = client.post("/api/guide", json={"soc": "2134", "message": "Will AI take this job?"}).json()
    assert "exposure is not a forecast of job losses" in ai["text"].lower()
    unrelated = client.post("/api/guide", json={"soc": "2134", "message": "Write me a poem about cheese"}).json()
    assert "career" in unrelated["text"].lower()
    assert "56,914" not in unrelated["text"]
    assert client.post("/api/guide", json={"soc": "9999", "message": "salary"}).status_code == 404


def test_api_health_and_dev_cors(client):
    assert client.get("/api/health").json()["status"] == "ok"
    response = client.options(
        "/api/bootstrap", headers={"Origin": "http://localhost:4175", "Access-Control-Request-Method": "GET"}
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:4175"


def test_display_sectors_follow_requested_career_not_borrowed_pathway(client):
    careers = {career["soc"]: career for career in client.get("/api/bootstrap").json()["careers"]}
    assert careers["2433"]["sector"] == "Finance and quantitative sciences"
    assert careers["3544"]["sector"] == "Data and analytics"
    assert careers["2142"]["sector"] == "Design and creative"
    from api.main import DISPLAY_SECTORS
    from pathfinder_ml import ML

    assert set(DISPLAY_SECTORS) == set(careers)
    for soc, career in careers.items():
        assert career["sector"] == DISPLAY_SECTORS[soc]
        assert career["metrics"] == ML().occupation(soc)["metrics"]
        assert career["history"] == ML().history(soc)


def test_ai_guide_discloses_preliminary_estimate_and_multi_code_range(client):
    answer = client.post("/api/guide", json={"soc": "2134", "message": "Explain automation exposure"}).json()["text"]
    assert "preliminary" in answer.lower()
    assert "several international job codes" in answer
    assert "weighted average" in answer
    assert "0.5126–0.5762" in answer


def test_pay_and_demand_guide_disclose_employee_coverage_and_provisional_year(client):
    for question in ("What is the pay?", "How much demand is there?"):
        text = client.post("/api/guide", json={"soc": "2134", "message": question}).json()["text"]
        assert "preliminary" in text.lower()
        assert "2025 figure is an ONS provisional estimate" in text
        assert "self-employed and freelance workers are not included" in text
