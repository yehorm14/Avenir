"""Exercise the assembled same-origin product, including the team's canonical API."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="module")
def client():
    from api.application import app

    return TestClient(app)


def test_experience_api_uses_the_contract_envelope_and_real_sources(client):
    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] and body["error"] is None
    assert len(body["data"]["careers"]) == 21
    assert body["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert body["meta"]["sources"]


def test_both_api_layers_share_validation_and_not_found_errors(client):
    for path in ("/api/careers/9999", "/api/v1/careers/9999"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
    invalid = client.post("/api/discovery", json={"mode": "bad"})
    assert invalid.status_code == 422
    assert invalid.json()["ok"] is False
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert invalid.json()["error"]["details"]


def test_production_decision_flow_works_without_keys_or_llm(client):
    response = client.post(
        "/api/v1/recommendations",
        json={
            "profile": {"interests": ["maths", "art_drawing", "design", "building_spaces"], "nation": "scotland"},
            "first_idea": "architect",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"]
    assert body["data"]["first_idea"]["soc2020"] == "2451"
    assert len(body["data"]["picks"]) == 3
    assert body["data"]["explanation"]["ai_written"] is False
    assert body["data"]["roadmap"]
    assert not any(source["status"] == "mock" for source in body["meta"]["sources"])


def test_openapi_describes_both_api_layers_and_consistent_envelopes(client):
    schema = client.get("/openapi.json").json()
    assert "/api/bootstrap" in schema["paths"]
    assert "/api/v1/recommendations" in schema["paths"]
    response = schema["paths"]["/api/bootstrap"]["get"]["responses"]["200"]
    assert "Envelope" in response["content"]["application/json"]["schema"]["$ref"]


def test_production_static_ui_is_served_after_api_routes(tmp_path):
    from api.application import create_application

    (tmp_path / "index.html").write_text("<!doctype html><title>Aventier production</title>")
    client = TestClient(create_application(web_dir=tmp_path))
    assert "Aventier production" in client.get("/").text
    assert client.get("/api/health").json()["data"]["status"] == "ok"
    assert client.get("/health").json()["data"]["status"] == "ok"


def test_excluded_sample_inputs_lower_decision_confidence_without_changing_real_metrics(client):
    from pathfinder_ml import ML

    from avenir_contracts import ProfileIn
    from avenir_decision import score_components

    data = client.app.state.data
    evidence = ML()
    scores = score_components(ProfileIn(interests=["computers_coding"]), list(data.careers.values()), data.affinity)
    assert scores["2134"].market_risk.confidence == "low"
    for soc, career in data.careers.items():
        for key, metric in evidence.occupation(soc)["metrics"].items():
            assert career.metrics[key].value == metric["value"]
        assert not any(metric.is_mock for metric in career.metrics.values())
