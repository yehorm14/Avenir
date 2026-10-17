from fastapi.testclient import TestClient
from pydantic import BaseModel

from avenir_api.app import create_app
from avenir_contracts import AvenirData


def test_unknown_route_is_not_found_envelope(data):
    r = TestClient(create_app(data=data)).get("/nope")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["meta"]["request_id"] == r.headers["X-Request-ID"]


def test_empty_data_health_reports_ml_missing():
    r = TestClient(create_app(data=AvenirData())).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["ml_mode"] == "missing"
    assert body["meta"]["sources"] == body["data"]["sources"]


def test_health_with_mock_data(data):
    body = TestClient(create_app(data=data)).get("/health").json()
    assert body["data"]["ml_mode"] == data.ml_mode
    assert body["data"]["sources"] == [s.model_dump(mode="json") for s in data.statuses]


def test_validation_error_envelope(data):
    app = create_app(data=data)

    class In(BaseModel):
        n: int

    @app.post("/echo")
    def echo(body: In):
        return body

    r = TestClient(app).post("/echo", json={"n": "x"})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["details"][0]["field"] == "body.n"


def test_unhandled_error_hides_traceback(data):
    app = create_app(data=data)

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret detail")

    r = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert r.status_code == 500
    assert r.json()["error"] == {"code": "INTERNAL", "message": "Something went wrong", "details": []}
    assert "secret" not in r.text


def test_state_and_cors(data):
    app = create_app(data=data)
    assert app.state.data is data
    assert app.state.ads and app.state.writer and app.state.suggester
    r = TestClient(app).get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_method_not_allowed_is_envelope_405(data):
    from fastapi.testclient import TestClient

    from avenir_api.app import create_app

    r = TestClient(create_app(data=data)).delete("/api/v1/tags")
    assert r.status_code == 405
    assert r.json()["ok"] is False


def test_unhandled_error_keeps_cors_header(data):
    # the browser drops a response without CORS headers, so the frontend would see a network error
    app = create_app(data=data)

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret detail")

    r = TestClient(app, raise_server_exceptions=False).get("/boom", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 500
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert r.json()["error"]["code"] == "INTERNAL"
    assert r.headers["x-request-id"] == r.json()["meta"]["request_id"]


def test_malformed_json_points_at_body(data):
    r = TestClient(create_app(data=data)).post(
        "/api/v1/recommendations", content=b"{bad", headers={"content-type": "application/json"}
    )
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "body"
