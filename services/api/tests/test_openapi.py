import json
from pathlib import Path

from avenir_api.app import create_app
from avenir_api.export_openapi import render
from avenir_contracts import AvenirData

EXPECTED = {
    "/health",
    "/api/v1/tags",
    "/api/v1/sources",
    "/api/v1/careers",
    "/api/v1/careers/{soc}",
    "/api/v1/careers/{soc}/history",
    "/api/v1/crises",
    "/api/v1/backtest/years",
    "/api/v1/backtest",
    "/api/v1/routes/{soc}",
    "/api/v1/profile",
    "/api/v1/recommendations",
    "/api/v1/careers/{soc}/hedge",
    "/api/v1/demo/live",
}
COMMITTED = Path(__file__).resolve().parents[3] / "docs" / "openapi.json"


def test_schema_has_every_path():
    schema = json.loads(render(create_app(data=AvenirData())))
    assert EXPECTED <= set(schema["paths"])


def test_committed_file_is_current():
    assert COMMITTED.read_text() == render(create_app(data=AvenirData()))


def _schema():
    return json.loads(render(create_app(data=AvenirData())))


def test_every_200_response_is_typed():
    for path, ops in _schema()["paths"].items():
        for method, op in ops.items():
            content = op["responses"]["200"]["content"]["application/json"]
            assert content["schema"] != {}, f"{method} {path} has an untyped 200 response"


def test_contract_models_in_components():
    names = set(_schema()["components"]["schemas"])
    assert {"RecommendationOut", "Career", "Hedge"} <= names


def test_documented_errors_are_envelopes():
    for path, ops in _schema()["paths"].items():
        for method, op in ops.items():
            for code in ("404", "422", "503", "500"):
                assert code in op["responses"], f"{method} {path} missing {code}"
            assert "HTTPValidationError" not in json.dumps(op["responses"]["422"])
