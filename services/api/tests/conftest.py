import warnings

with warnings.catch_warnings():
    # Starlette's TestClient warns about httpx at import; third-party noise, not ours.
    warnings.simplefilter("ignore")
    import fastapi.testclient  # noqa: F401

from pathlib import Path

import pytest

from avenir_contracts import load_data
from avenir_contracts import mock as contracts_mock

# Pinned to the ML mock files so these tests don't change when Arsenii's real data lands;
# test_freeze.py is the one check that reads the real data.
ML_MOCK = Path(__file__).resolve().parents[3] / "snapshots" / "ml" / "mock"


@pytest.fixture(scope="session")
def data(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("snaps")
    # Pin catalogue generation too: its seeded metrics depend on ML occupation order.
    with pytest.MonkeyPatch.context() as env:
        env.setenv("PATHFINDER_ML_DIR", str(ML_MOCK))
        contracts_mock.write(tmp / "mock")
    return load_data(ml_dir=ML_MOCK, snapshot_dir=tmp)


@pytest.fixture(autouse=True)
def _no_live_model(monkeypatch):
    """Tests never call a real model. A local .env (loaded with setdefault) must not switch the
    explanation writer on, so these are set explicitly rather than deleted."""
    monkeypatch.setenv("LLM_ENABLED", "0")
    for name in ("LLM_API_KEY", "LLM_API_KEY_2", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEY_2"):
        monkeypatch.setenv(name, "")
