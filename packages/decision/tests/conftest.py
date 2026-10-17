"""Shared fixtures for the decision engine tests.

The data set is the contract mock data, written to a temp dir and loaded through the same
loader the API uses, so tests see the real AvenirData shape. ML mocks come from
snapshots/ml/mock/ via pathfinder_ml.ML().
"""
from __future__ import annotations

import pytest

from avenir_contracts import AvenirData, Career, ProfileIn, Qualification, load_data
from avenir_contracts import mock as contract_mock


@pytest.fixture(scope="session")
def data(tmp_path_factory: pytest.TempPathFactory) -> AvenirData:
    tmp = tmp_path_factory.mktemp("snapshots")
    contract_mock.write(tmp / "mock")
    return load_data(snapshot_dir=tmp)


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
