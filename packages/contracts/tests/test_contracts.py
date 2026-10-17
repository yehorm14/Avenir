import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from avenir_contracts import (
    CATALOGUE_METRICS,
    ML_METRICS,
    KeywordSuggester,
    Metric,
    ProfileIn,
    RecommendationRequest,
    SnapshotAds,
    load_data,
)
from avenir_contracts.mock import write

ML_MOCK = Path(__file__).resolve().parents[3] / "snapshots" / "ml" / "mock"


@pytest.fixture
def data(tmp_path):
    write(tmp_path / "mock")
    return load_data(ml_dir=tmp_path / "no_real_ml", snapshot_dir=tmp_path)


def test_ml_metric_parses_unchanged():
    occ = json.loads((ML_MOCK / "occupations.json").read_text())["occupations"][0]
    m = Metric.model_validate(occ["metrics"]["pay_median"])
    assert m.unit == "GBP/year" and m.region == "UK" and "employees_only" in m.flags


def test_unknown_metric_fields_ignored():
    m = Metric.model_validate({"value": 1, "unit": "x", "source": "s", "confidence": "low", "new_field": 3})
    assert m.value == 1


def test_missing_metric_shape():
    m = Metric.missing("count", "adzuna")
    assert m.is_missing and m.status == "pending" and m.confidence == "low"


@pytest.mark.parametrize("bad", [
    {"automation_worry": 1.5}, {"free_text": "x" * 301}, {"unknown_field": 1}, {"interests": ["x"] * 17},
])
def test_profile_validation(bad):
    with pytest.raises(ValidationError):
        ProfileIn(**bad)


def test_first_idea_required():
    with pytest.raises(ValidationError):
        RecommendationRequest(profile=ProfileIn(), first_idea="")


def test_join_gives_20_careers_with_ml_and_catalogue_metrics(data):
    assert len(data.careers) == 20
    arch = data.careers["2451"]
    assert arch.official_title == "Architects" and arch.title
    assert set(arch.metrics) <= set(ML_METRICS) | set(CATALOGUE_METRICS)  # no unknown keys
    v1_0 = set(ML_METRICS) - {"young_worker_share"}  # v1.0 mocks lack the v1.1 metric
    assert v1_0 <= set(arch.metrics)
    assert {"shortage", "wellbeing", "stress", "ads_now"} <= set(arch.metrics)
    assert arch.entry_subjects == ["maths", "art", "physics"]


def test_everything_else_loads(data):
    assert data.tags and data.affinity and data.backtest and data.crises and data.sources
    assert all(len(v) <= 5 for v in data.hedges.values())
    hist = data.history["2134"]
    years = [pt.year for pt in hist]
    assert years[0] <= 2011 and years == sorted(set(years))  # v1.0 starts 2011, v1.1 starts 2007
    assert all(pt.jobs_k is None for pt in hist if pt.year < 2011)  # before 2011 only pay
    assert data.routes["2451"][0].nation == "scotland"
    names = {s.name: s.status for s in data.statuses}
    assert names["catalogue"] == "mock" and names["routes"] == "mock"
    assert names["ml_occupations"] == "snapshot"  # preliminary real values in Arsenii's mock


def test_no_catalogue_still_loads(tmp_path):
    d = load_data(snapshot_dir=tmp_path)
    assert len(d.careers) == 20 and d.careers["2134"].title == "Software developer"
    assert {s.name: s.status for s in d.statuses}["catalogue"] == "missing"


def test_keyword_suggester_uses_ml_tags():
    out = KeywordSuggester().suggest("I like drawing and fixing bikes")
    assert {m.tag for m in out} & {"art_drawing", "fixing_hands_on"}
    assert KeywordSuggester().suggest("") == []


def test_snapshot_ads(data):
    m, st = SnapshotAds().ads_now(data.careers["2451"], "UK")
    assert st.status == "mock" and m.unit == "count"
