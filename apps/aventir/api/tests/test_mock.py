"""The demo must work with no imported database, credentials or provider calls."""

import pytest
from aventir import main
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("AVENTIR_MODE", "mock")
    with TestClient(main.create_app(database=tmp_path / "absent.sqlite3", api_key="")) as app:
        yield app


def test_mock_mode_never_initialises_openai_even_when_a_key_is_present(monkeypatch, tmp_path):
    monkeypatch.setenv("AVENTIR_MODE", "mock")

    def forbidden(*args, **kwargs):
        raise AssertionError("Mock mode must never initialise an external provider")

    monkeypatch.setattr(main, "AsyncOpenAI", forbidden)
    with TestClient(main.create_app(database=tmp_path / "missing.sqlite3", api_key="unused-test-key")) as app:
        health = app.get("/api/health").json()
        assert health["mode"] == "mock"
        assert health["database_ready"] is True
        assert health["ai_configured"] is False
        assert health["research_available"] is True


def test_mock_catalogue_supports_search_filters_and_pagination_without_sqlite(client):
    first = client.get("/api/careers?limit=8").json()
    assert first.get("total") == 20
    second = client.get("/api/careers?limit=8&offset=8").json()
    assert len(first["items"]) == len(second["items"]) == 8
    assert not {c["id"] for c in first["items"]} & {c["id"] for c in second["items"]}
    search = client.get("/api/careers", params={"q": "software developer"}).json()
    assert any(c["title"] == "software developer" for c in search["items"])
    assert client.get("/api/careers", params={"q": "%"}).json()["total"] == 0
    trades = client.get("/api/careers", params={"group": "Craft and trades"}).json()
    assert trades["total"] > 0 and all(c["group"] == "Craft and trades" for c in trades["items"])


def test_mock_coverage_is_labelled_and_missing_evidence_stays_missing(client):
    meta = client.get("/api/meta").json()
    assert meta.get("mode") == "mock"
    assert meta["occupation_count"] == 20
    assert sum(g["count"] for g in meta["groups"]) == 20
    assert meta["industries"] and all(s["points"] for s in meta["industries"])
    rows = client.get("/api/careers?limit=100").json()["items"]
    missing = next(c for c in rows if c["salary"] is None and c["sector_id"] is None)
    detail = client.get("/api/careers/" + missing["id"]).json()
    assert detail["salary"] is None and detail["industry"] is None
    assert detail["data_status"] == "sample"


def test_mock_research_returns_a_deterministic_labelled_sample(client):
    rows = client.get("/api/careers?limit=100").json().get("items", [])
    assert rows, "Mock careers must be available without a database import"
    career = next(c for c in rows if c["title"] == "software developer")
    body = {"career_id": career["id"], "question": "What apprenticeship routes should I explore?"}
    response = client.post("/api/research", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["is_mock"] is True and data["model"] == "mock"
    assert len(data["considerations"]) == 3 and data["sources"]
    assert data == client.post("/api/research", json=body).json()
    assert "apprenticeship" in data["summary"].lower()


def test_mock_mode_preserves_request_validation_and_unknown_career_errors(client):
    assert client.get("/api/careers/unknown").status_code == 404
    assert client.post("/api/research", json={"career_id": "unknown"}).status_code == 404
    assert client.get("/api/careers?limit=101").status_code == 422
    assert client.get("/api/careers?offset=-1").status_code == 422
    assert client.post("/api/research", json={"career_id": "a", "question": "x" * 601}).status_code == 422


def test_explicit_live_mode_does_not_silently_substitute_fixtures(monkeypatch, tmp_path):
    monkeypatch.setenv("AVENTIR_MODE", "mock")
    with TestClient(main.create_app(database=tmp_path / "absent.sqlite3", api_key="", mode="live")) as app:
        assert app.get("/api/health").json()["mode"] == "live"
        assert app.get("/api/careers").status_code == 503


def test_invalid_mode_is_rejected_instead_of_silently_using_live_credentials():
    with pytest.raises(ValueError, match="AVENTIR_MODE"):
        main.create_app(mode="typo")
