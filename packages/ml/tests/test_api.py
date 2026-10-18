"""Contract tests for the ML artefacts and the pathfinder_ml interface.

Run from the repo root: python -m pytest packages/ml/tests -q
They read snapshots/ml/mock, so they pass without any private data.
"""
import json
from pathlib import Path

import pytest

from pathfinder_ml import ARTEFACTS, FLAG_TEXT, ML, MUST_MENTION

ROOT = Path(__file__).resolve().parents[3]
REAL = ROOT / "snapshots" / "ml"
MOCK = REAL / "mock"
SCHEMA = json.loads((ROOT / "packages" / "ml" / "schemas" / "ml_artefacts.schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ml(tmp_path_factory):
    empty = tmp_path_factory.mktemp("no_real_artefacts")
    return ML(data_dir=empty, mock_dir=MOCK)


@pytest.mark.parametrize("folder", [MOCK, REAL], ids=["mock", "real"])
@pytest.mark.parametrize("name", ARTEFACTS)
def test_artefact_matches_its_schema(name, folder):
    jsonschema = pytest.importorskip("jsonschema")
    path = folder / f"{name}.json"
    if not path.is_file():
        pytest.skip(f"{path} not built yet")
    schema = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{name}_file"}
    data = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)
    assert data["schema_version"] == "1.2"


def test_real_artefacts_cover_every_occupation_and_the_demo_set():
    path = REAL / "occupations.json"
    if not path.is_file():
        pytest.skip("real artefacts not built yet")
    data = json.loads(path.read_text(encoding="utf-8"))
    socs = {o["soc2020"] for o in data["occupations"]}
    assert len(socs) == 412
    assert set(data["demo_set"]) <= socs
    real = ML(data_dir=REAL, mock_dir=MOCK)
    assert real.status()["mode"] in {"real", "mixed"}


def test_falls_back_to_mock_and_reports_it(ml):
    status = ml.status()
    assert status["mode"] == "mock"
    for name, info in status["artefacts"].items():
        assert info["status"] != "missing", name
        assert info["origin"] == "mock"
        assert Path(info["path"]).parent == MOCK


def test_mixed_mode_when_only_some_real_files_exist(tmp_path):
    (tmp_path / "sources.json").write_text((MOCK / "sources.json").read_text(encoding="utf-8"), encoding="utf-8")
    status = ML(data_dir=tmp_path, mock_dir=MOCK).status()
    assert status["mode"] == "mixed"
    assert status["artefacts"]["sources"]["origin"] == "real"
    assert status["artefacts"]["occupations"]["origin"] == "mock"


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


@pytest.mark.parametrize("text,bad", [("I want an apprenticeship", "computers_coding"), ("a powerful speaker", "electricity_energy"),
                                      ("artificial intelligence", "art_drawing"), ("I like apples", "computers_coding")])
def test_match_tags_has_no_substring_hits(ml, text, bad):
    assert bad not in [r["tag"] for r in ml.match_tags(text)]


def test_match_tags_finds_each_tag_from_its_own_label(ml):
    for tag in ml.tags():
        assert tag["id"] in [r["tag"] for r in ml.match_tags(f"I enjoy {tag['label'].lower()}", top_k=16)], tag["id"]
    assert [r["tag"] for r in ml.match_tags("I enjoy helping people")][:1] == ["helping_people"]
    assert ml.match_tags("I love math")[0]["score"] == ml.match_tags("I love maths")[0]["score"]
    assert "fixing_hands_on" in [r["tag"] for r in ml.match_tags("I like hands-on work")]


def test_match_tags_validates_input(ml):
    with pytest.raises(ValueError):
        ml.match_tags("maths", top_k=-1)
    with pytest.raises(TypeError):
        ml.match_tags(None)


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
    windows = json.loads((MOCK / "backtest.json").read_text(encoding="utf-8"))["windows"]
    latest = ml.backtest()
    assert latest["jobs_comparable"] is True
    assert latest["base_year"] == max(w["base_year"] for w in windows if w["jobs_comparable"])
    assert ml.backtest_years() == sorted(w["base_year"] for w in windows)
    for w in windows:
        assert [g["key"] for g in w["groups"]] == ["ambitious", "balanced", "safe", "all"]
        assert {o["group_then"] for o in w["occupations"]} <= {"ambitious", "safe", "other"}
    with pytest.raises(KeyError):
        ml.backtest(1990)
    for year in ml.backtest_years():
        w = ml.backtest(year)
        if w["outcome_year"] > 2020:
            assert w["jobs_comparable"] is False
            assert all(g["jobs_growth"] is None for g in w["groups"])
    assert ml.backtest_caveats()


def test_history_flags_follow_the_rules(ml):
    for occ in ml.occupations():
        for p in ml.history(occ["soc2020"]):
            assert ("bridged_soc2010" in p["flags"]) == (p["year"] <= 2020)
            assert ("bridged_soc2000" in p["flags"]) == (p["year"] <= 2010)
            assert ("recoded_2021" in p["flags"]) == (p["year"] >= 2021)
            assert ("covid_year" in p["flags"]) == (p["year"] == 2020)
            if p["year"] <= 2010:
                assert p["jobs_k"] is None  # job counts are not carried across two code changes


FOLDERS = {"mock": MOCK, "real": REAL}
CAP_LOW = {"mock", "cv_high", "imputed_parent", "bridged_low_purity", "partial_sources", "suppressed", "pending_source"}
CAP_MEDIUM = {"bridged_soc2010", "bridged_soc2000", "multi_isco", "category_level", "covid_year", "ons_indicative_counts",
              "sources_disagree", "fallback_all_employees"}


def _load(folder, name):
    path = folder / f"{name}.json"
    if not path.is_file():
        pytest.skip(f"{path} not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(params=list(FOLDERS))
def folder(request):
    return FOLDERS[request.param]


def test_confidence_follows_the_contract_rule(folder):
    bad = []
    for o in _load(folder, "occupations")["occupations"]:
        for k, m in o["metrics"].items():
            flags = set(m["flags"])
            if m["value"] is None and m["confidence"] != "low":
                bad.append((o["soc2020"], k, "null not low"))
            if m["value"] is not None and flags & CAP_LOW and m["confidence"] != "low":
                bad.append((o["soc2020"], k, "should be low"))
            if m["confidence"] == "high" and flags & CAP_MEDIUM:
                bad.append((o["soc2020"], k, "should be at most medium"))
    assert not bad, bad[:5]


def test_values_ranges_and_missing(folder):
    for o in _load(folder, "occupations")["occupations"]:
        for k, m in o["metrics"].items():
            assert (m["low"] is None) == (m["high"] is None), (o["soc2020"], k)
            assert (m["value"] is None) == ("suppressed" in m["flags"]), (o["soc2020"], k)
            if m["value"] is not None and m["low"] is not None:
                assert m["low"] <= m["value"] <= m["high"], (o["soc2020"], k)


def test_references_resolve(folder):
    socs = {o["soc2020"] for o in _load(folder, "occupations")["occupations"]}
    assert {h["soc2020"] for v in _load(folder, "hedges")["occupations"].values() for h in v} <= socs
    assert {o["soc2020"] for w in _load(folder, "backtest")["windows"] for o in w["occupations"]} <= socs
    occ = _load(folder, "occupations")
    assert len(occ["demo_set"]) == 20
    assert set(occ["demo_set"]) == {o["soc2020"] for o in occ["occupations"] if o["in_demo_set"]}


def test_history_years_increase(folder):
    for soc, pts in _load(folder, "history")["occupations"].items():
        years = [p["year"] for p in pts]
        assert years == sorted(set(years)) and all(2007 <= y <= 2025 for y in years), soc


def test_crises_are_centred_and_gated():
    occ = _load(REAL, "occupations")["occupations"]
    crises = {c["key"]: c for c in _load(REAL, "crises")["crises"]}
    for key, metric_key in (("covid", "resilience_covid"), ("cost_of_living", "resilience_cost_of_living"),
                            ("tech_slump", "resilience_tech_slump"), ("gfc_2008", "resilience_2008")):
        vals = sorted(o["metrics"][metric_key]["value"] for o in occ if o["metrics"][metric_key]["value"] is not None)
        assert abs(vals[len(vals) // 2]) < 0.01, key
        assert isinstance(crises[key]["show_on_card"], bool)
    assert crises["gfc_2008"]["show_on_card"] is False  # fails the placebo test


def test_committed_fit_is_not_the_placeholder():
    fit = _load(REAL, "fit")
    assert fit["status"] != "mock" and "evaluation" in fit


def test_status_never_raises(tmp_path):
    (tmp_path / "fit.json").write_bytes(bytes([0xEF, 0xBB, 0xBF]) + b"{}")
    (tmp_path / "eval.json").write_text("[]", encoding="utf-8")
    (tmp_path / "sources.json").write_text("{oops", encoding="utf-8")
    status = ML(data_dir=tmp_path, mock_dir=MOCK).status()
    assert status["artefacts"]["fit"]["origin"] == "real"
    assert status["artefacts"]["eval"]["status"] == "invalid"
    assert status["artefacts"]["sources"]["status"] == "invalid"
    assert status["mode"] == "mixed"


def test_mock_copies_do_not_drift():
    for name in ("crises", "sources", "fit"):
        real, mock = _load(REAL, name), _load(MOCK, name)
        real.pop("generated_at", None)
        mock.pop("generated_at", None)
        assert real == mock, name


def test_public_accessors(ml):
    years = ml.backtest_years()
    assert years == sorted(years) and years
    assert all(ml.backtest(y)["base_year"] == y for y in years)
    aff = ml.affinity()
    assert set(aff) == {t["id"] for t in ml.tags()}
    assert all(0.0 <= v <= 1.0 for row in aff.values() for v in row.values())
    aff["maths"].clear()  # a copy: the loader's table is unchanged
    assert ml.affinity()["maths"]

