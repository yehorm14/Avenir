"""Shared fixtures for the decision engine tests.

The data set is the contract mock data, written to a temp dir and loaded through the same
loader the API uses, so tests see the real AvenirData shape. ML data is pinned to
snapshots/ml/mock/ (ML_MOCK), never the real artefacts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from avenir_contracts import AvenirData, Career, ProfileIn, Qualification, load_data
from avenir_contracts import mock as contract_mock

# Pinned to the ML mock files so these tests don't change when Arsenii's real data lands;
# test_freeze.py is the one check that reads the real data.
ML_MOCK = Path(__file__).resolve().parents[3] / "snapshots" / "ml" / "mock"


@pytest.fixture(scope="session")
def data(tmp_path_factory: pytest.TempPathFactory) -> AvenirData:
    tmp = tmp_path_factory.mktemp("snapshots")
    contract_mock.write(tmp / "mock")
    return load_data(ml_dir=ML_MOCK, snapshot_dir=tmp)


@pytest.fixture
def careers(data: AvenirData) -> list[Career]:
    return list(data.careers.values())


@pytest.fixture
def amira() -> ProfileIn:
    return ProfileIn(
        interests=["maths", "art_drawing", "design", "building_spaces"],
        qualifications=[
            Qualification(subject="maths", level="higher"),
            Qualification(subject="art", level="higher"),
        ],
        nation="scotland",
        automation_worry=0.5,
    )
