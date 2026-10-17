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
