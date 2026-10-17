"""Contract tests for the ML artefacts and the pathfinder_ml interface.

Run from the repo root: python -m pytest packages/ml/tests -q
They read snapshots/ml/mock, so they pass without any private data.
"""
import json
from pathlib import Path

import pytest

from pathfinder_ml import ARTEFACTS, FLAG_TEXT, ML, MUST_MENTION

ROOT = Path(__file__).resolve().parents[3]
MOCK = ROOT / "snapshots" / "ml" / "mock"
SCHEMA = json.loads((ROOT / "packages" / "ml" / "schemas" / "ml_artefacts.schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ml(tmp_path_factory):
    empty = tmp_path_factory.mktemp("no_real_artefacts")
    return ML(data_dir=empty, mock_dir=MOCK)


@pytest.mark.parametrize("name", ARTEFACTS)
def test_mock_file_matches_its_schema(name):
    jsonschema = pytest.importorskip("jsonschema")
    schema = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{name}_file"}
    data = json.loads((MOCK / f"{name}.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)


def test_falls_back_to_mock_and_reports_it(ml):
    status = ml.status()
    assert status["mode"] in {"mock", "mixed"}
    for name, info in status["artefacts"].items():
        assert info["status"] != "missing", name
        assert Path(info["path"]).parent == MOCK


def test_flag_vocabulary_is_complete():
    schema_flags = set(SCHEMA["$defs"]["flag"]["enum"])
    assert schema_flags == set(FLAG_TEXT)
    assert MUST_MENTION <= schema_flags


def test_every_metric_cites_a_known_source(ml):
    sources = ml.sources()
    for occ in ml.occupations():
        for key, m in occ["metrics"].items():
            assert m["source"] in sources, (occ["soc2020"], key)
            if m["status"] == "pending":
                assert m["value"] is None and "pending_source" in m["flags"], (occ["soc2020"], key)


def test_demo_set_is_consistent(ml):
    raw = json.loads((MOCK / "occupations.json").read_text(encoding="utf-8"))
    demo = ml.occupations(demo_only=True)
    assert len(raw["demo_set"]) == 20
    assert {o["soc2020"] for o in demo} == set(raw["demo_set"])


def test_unknown_occupation_is_empty_not_an_error(ml):
    assert ml.occupation("9999") is None
    assert ml.history("9999") == []
    assert ml.hedges("9999") == []


def test_results_are_copies(ml):
    first = ml.occupation("2134")
    first["metrics"]["pay_median"]["value"] = -1
    assert ml.occupation("2134")["metrics"]["pay_median"]["value"] != -1


def test_match_tags_keyword_baseline(ml):
    tags = [r["tag"] for r in ml.match_tags("I like drawing and fixing bikes")]
    assert "art_drawing" in tags and "fixing_hands_on" in tags
    assert ml.match_tags("") == []
    assert ml.match_tags("I like drawing") == ml.match_tags("I like drawing")
    assert all(0 < r["score"] < 1 for r in ml.match_tags("maths, coding and data"))


def test_fit_scores(ml):
    with pytest.raises(ValueError, match="unknown tag ids"):
        ml.fit_scores(["not_a_tag"])
    assert ml.fit_scores([]) == {}
    a = ml.fit_scores(["maths", "art_drawing"])
    b = ml.fit_scores(["art_drawing", "maths"])
    assert a == b
    assert set(a) == {o["soc2020"] for o in ml.occupations()}
    assert all(0.0 <= v <= 1.0 for v in a.values())


def test_hedges_are_sorted_and_exclude_self(ml):
    for occ in ml.occupations():
        hs = ml.hedges(occ["soc2020"], k=5)
        sims = [h["similarity"] for h in hs]
        assert sims == sorted(sims, reverse=True)
        assert occ["soc2020"] not in {h["soc2020"] for h in hs}
    with pytest.raises(ValueError):
        ml.hedges("2134", k=-1)


def test_backtest_windows(ml):
    latest = ml.backtest()
    assert latest["base_year"] == max(w["base_year"] for w in json.loads((MOCK / "backtest.json").read_text(encoding="utf-8"))["windows"])
    with pytest.raises(KeyError):
        ml.backtest(1990)
    for year in (2013, 2014, 2019):
        w = ml.backtest(year)
        if w["outcome_year"] > 2020:
            assert w["jobs_comparable"] is False
            assert all(g is None or g["jobs_growth"] is None for g in w["groups"])
    assert ml.backtest_caveats()


def test_history_flags_follow_the_rules(ml):
    for occ in ml.occupations():
        for p in ml.history(occ["soc2020"]):
            assert ("bridged_soc2010" in p["flags"]) == (p["year"] <= 2020)
            assert ("recoded_2021" in p["flags"]) == (p["year"] >= 2021)
            assert ("covid_year" in p["flags"]) == (p["year"] == 2020)
