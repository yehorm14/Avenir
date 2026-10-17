import json
from types import SimpleNamespace

import httpx
import pytest
from aventir.database import connect, initialise, save_career
from aventir.main import Reflection, create_app
from fastapi.testclient import TestClient
from openai import AuthenticationError


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.sqlite3"
    conn = connect(path)
    initialise(conn)
    for i, title in enumerate(["Software developer", "Civil engineer", "100% tester"]):
        save_career(
            conn,
            {
                "id": str(i),
                "title": title,
                "group": "Professionals",
                "aliases": [],
                "essential": [{"title": "programming", "kind": "skill"}],
                "optional": [],
                "description": "A real occupation",
                "source_url": "https://example.org",
                "salary": None,
                "sector_id": "technology" if i == 0 else None,
            },
        )
    conn.execute(
        "INSERT INTO series VALUES (?,?)",
        (
            "technology",
            json.dumps(
                {
                    "id": "technology",
                    "name": "Information & communication",
                    "frequency": "Three-month average",
                    "source_url": "https://www.ons.gov.uk/example",
                    "granularity": "industry",
                    "points": [{"time": "2025-01-01", "value": 40000}],
                }
            ),
        ),
    )
    conn.execute("INSERT INTO metadata VALUES (?,?)", ("catalogue", json.dumps({"occupation_count": 3})))
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def client(database):
    with TestClient(create_app(database, api_key="", mode="live")) as c:
        yield c


def test_search_pagination_and_literal_metacharacters(client):
    data = client.get("/api/careers", params={"q": "engineer"}).json()
    assert data["total"] == 1 and data["items"][0]["id"] == "1"
    assert client.get("/api/careers", params={"q": "%"}).json()["total"] == 1
    assert len(client.get("/api/careers?limit=1&offset=1").json()["items"]) == 1
    assert client.get("/api/careers?offset=-1").status_code == 422


def test_detail_only_includes_matched_industry_context(client):
    data = client.get("/api/careers/0").json()
    assert data["industry"]["granularity"] == "industry"
    assert data["salary"] is None
    assert client.get("/api/careers/1").json()["industry"] is None
    assert client.get("/api/careers/missing").status_code == 404


def test_ai_is_explicitly_unavailable_without_secret_and_validates_input(client):
    assert client.get("/api/health").json()["ai_configured"] is False
    assert (
        client.post(
            "/api/research", json={"career_id": "0", "question": "What should I explore?"}
        ).status_code
        == 503
    )
    assert client.post("/api/research", json={"career_id": "0", "question": "x" * 601}).status_code == 422
    assert client.post("/api/research", json={"career_id": "missing"}).status_code == 404


def test_catalogue_metadata_is_exposed_without_any_credentials(client):
    data = client.get("/api/meta").json()
    assert data["occupation_count"] == 3
    assert len(data["groups"]) == 1
    assert "key" not in str(data).lower()


def test_ai_receives_server_side_evidence_and_returns_structured_reflection(database):
    calls = []

    async def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            output_parsed=Reflection(
                summary="Explore what building software feels like.",
                considerations=[
                    "Try a small project",
                    "Investigate training routes",
                    "Ask about the daily work",
                ],
                next_question="What kinds of problems do you enjoy?",
            )
        )

    provider = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    with TestClient(create_app(database, api_key="", ai_client=provider, mode="live")) as c:
        result = c.post("/api/research", json={"career_id": "0", "question": "Do I need a degree?"})
        assert result.status_code == 200
        assert result.json()["career_id"] == "0"
        assert len(result.json()["considerations"]) == 3
        assert result.json()["sources"] == ["https://example.org", "https://www.ons.gov.uk/example"]
        context = json.loads(calls[0]["input"][1]["content"])
        assert context["evidence"]["essential_skills"] == ["programming"]
        assert context["evidence"]["industry_context"]["recent_observations"][0]["value"] == 40000
        assert calls[0]["text_format"] is Reflection


def test_provider_errors_never_expose_credentials_or_response_bodies(database):
    async def parse(**kwargs):
        raise AuthenticationError(
            "Sensitive provider body must not be exposed",
            response=httpx.Response(
                401, request=httpx.Request("POST", "https://api.openai.com/v1/responses")
            ),
            body={"secret": "must-not-leak"},
        )

    with TestClient(
        create_app(
            database,
            api_key="",
            ai_client=SimpleNamespace(responses=SimpleNamespace(parse=parse)),
            mode="live",
        )
    ) as c:
        response = c.post("/api/research", json={"career_id": "0"})
        assert response.status_code == 502
        assert "Sensitive" not in response.text
        assert "must-not-leak" not in response.text
        assert "valid backend API key" in response.json()["detail"]
