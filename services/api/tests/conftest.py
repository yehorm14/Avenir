import warnings

with warnings.catch_warnings():
    # Starlette's TestClient warns about httpx at import; third-party noise, not ours.
    warnings.simplefilter("ignore")
    import fastapi.testclient  # noqa: F401

import pytest

from avenir_contracts import load_data
from avenir_contracts import mock as contracts_mock


@pytest.fixture(scope="session")
def data(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("snaps")
    contracts_mock.write(tmp / "mock")
    return load_data(snapshot_dir=tmp)
