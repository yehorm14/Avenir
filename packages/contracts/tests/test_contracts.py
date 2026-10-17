import pytest
from pydantic import ValidationError

from avenir_contracts import (
    METRIC_UNITS,
    Metric,
    ProfileIn,
    RecommendationRequest,
    SnapshotAds,
    load_snapshots,
)
from avenir_contracts.mock import write


def test_missing_metric_must_be_low_confidence():
    with pytest.raises(ValidationError):
        Metric(value=None, unit="pct", source="x", region="UK", granularity="occupation", confidence="high")
    assert Metric.missing("pct", "ashe_t14").is_missing


def test_low_above_high_rejected():
    with pytest.raises(ValidationError):
        Metric(value=1, low=5, high=2, unit="pct", source="x", region="UK",
               granularity="occupation", confidence="low")


@pytest.mark.parametrize("bad", [
    {"automation_worry": 1.5},
    {"free_text": "x" * 301},
    {"interests": ["juggling"]},
    {"unknown_field": 1},
])
def test_profile_validation(bad):
    with pytest.raises(ValidationError):
        ProfileIn(**bad)


def test_first_idea_required():
    with pytest.raises(ValidationError):
        RecommendationRequest(profile=ProfileIn(), first_idea="")


def test_mock_round_trip(tmp_path):
    write(tmp_path / "mock")
    snap = load_snapshots(tmp_path)
    assert len(snap.careers) == 20
    assert {s.status for s in snap.statuses} == {"mock"}
    c = next(iter(snap.careers.values()))
    assert c.soc2020.startswith("00")
    for name, unit in METRIC_UNITS.items():
        assert getattr(c.metrics, name).unit == unit
    assert set(snap.backtest) == set(range(2010, 2020))
    assert all(len(v) == 3 for v in snap.hedges.values())


def test_missing_snapshots_reported(tmp_path):
    snap = load_snapshots(tmp_path)
    assert snap.careers == {}
    assert {s.status for s in snap.statuses} == {"missing"}


def test_snapshot_ads_never_live():
    snap_c = next(iter(load_snapshots().careers.values()), None)
    if snap_c is None:
        pytest.skip("no snapshots")
    m, st = SnapshotAds().ads_now(snap_c, "UK")
    assert st.status in {"mock", "snapshot", "missing"}
