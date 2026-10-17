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
    contracts_mock.write(tmp / "mock")
    return load_data(ml_dir=ML_MOCK, snapshot_dir=tmp)
