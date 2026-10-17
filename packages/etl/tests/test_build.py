"""Catalogue ETL: curated CSV -> CatalogueFile -> snapshots/catalogue.json."""
from __future__ import annotations

from pathlib import Path

import pytest

from avenir_contracts.catalogue import CatalogueFile
from avenir_contracts.data import load_data
from avenir_contracts.vocab import CATALOGUE_METRICS
from avenir_etl.build import build_catalogue, demo_socs, main
from avenir_etl.curated import CuratedError, load_curated

FIX = Path(__file__).parent / "fixtures"
OK = FIX / "occupations_ok.csv"
BAD = FIX / "occupations_bad.csv"
ROUTES = FIX / "routes_ok.csv"
SOCS = {"2451", "2134", "2433", "3544"}


def test_load_curated_ok_splits_lists_and_normalises():
    entries = load_curated(OK, SOCS)
    assert [e.soc2020 for e in entries] == ["2451", "2134", "2433"]
    architect, dev, actuary = entries
    assert architect.title == "Architect"
    assert architect.aliases == ["architecture", "building designer"]
    assert architect.entry_subjects == ["maths", "art", "physics"]
    assert architect.description == "Designs buildings and the spaces around them."
    assert dev.description is None
    assert actuary.aliases == []
    assert all(e.metrics == {} for e in entries)


def test_load_curated_bad_names_every_bad_row():
    with pytest.raises(CuratedError) as exc:
        load_curated(BAD, SOCS)
    msg = str(exc.value)
    assert isinstance(exc.value, ValueError)
    assert "line 2 (soc2020 2451)" in msg and "verified_by" in msg
    assert "line 3 (soc2020 9999)" in msg and "demo set" in msg
    assert "line 4 (soc2020 2134)" in msg and "astrology" in msg
    assert "line 6 (soc2020 2433)" in msg and "duplicate" in msg
    assert "line 7 (soc2020 3544)" in msg and "title" in msg
    assert "line 5" not in msg


def test_load_curated_unknown_soc_not_in_demo_set():
    with pytest.raises(CuratedError, match="2134"):
        load_curated(OK, {"2451", "2433"})


def test_build_catalogue_valid_file_with_four_metrics():
    cat = build_catalogue(load_curated(OK, SOCS))
    again = CatalogueFile.model_validate_json(cat.model_dump_json())
    assert again == cat
    assert cat.status == "preliminary"
    assert len(cat.entries) == 3
    for e in cat.entries:
        assert set(e.metrics) == set(CATALOGUE_METRICS)
        for key, unit in CATALOGUE_METRICS.items():
            assert e.metrics[key].unit == unit
            assert e.metrics[key].is_missing
        assert e.metrics["wellbeing"].granularity == "major_group"
        assert e.metrics["stress"].granularity == "major_group"


def test_build_catalogue_generated_at_override():
    cat = build_catalogue(load_curated(OK, SOCS), generated_at="2026-10-17T00:00:00+00:00")
    assert cat.generated_at == "2026-10-17T00:00:00+00:00"


def test_shortage_missing_without_oid_file(tmp_path):
    for oid in (None, tmp_path / "nope.xlsx"):
        cat = build_catalogue(load_curated(OK, SOCS), oid)
        for e in cat.entries:
            m = e.metrics["shortage"]
            assert m.is_missing and m.source == "oid_2025" and "not loaded" in m.note


def test_shortage_from_oid_parser(tmp_path, monkeypatch):
    import sys
    import types

    oid = tmp_path / "oid.xlsx"
    oid.write_bytes(b"")
    from avenir_contracts.metric import Metric

    flag = Metric(value=1.0, unit="flag", source="oid_2025", confidence="medium", status="final")
    parse = types.ModuleType("avenir_adapters.occupations_in_demand.parse")
    parse.oid_shortage = lambda path: {"2451": flag}
    for name in ("avenir_adapters", "avenir_adapters.occupations_in_demand"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, "avenir_adapters.occupations_in_demand.parse", parse)
    monkeypatch.setattr(sys.modules["avenir_adapters.occupations_in_demand"], "parse", parse, raising=False)

    cat = build_catalogue(load_curated(OK, SOCS), oid)
    by_soc = {e.soc2020: e for e in cat.entries}
    assert by_soc["2451"].metrics["shortage"].value == 1.0
    assert by_soc["2134"].metrics["shortage"].is_missing  # SOC absent from parsed dict


def test_demo_socs_matches_ml_mock():
    socs = demo_socs()
    assert len(socs) == 20
    assert {"2451", "2134", "2313"} <= socs


def test_cli_writes_catalogue_json_and_it_loads(tmp_path):
    out = tmp_path / "snap"
    assert main(["--curated", str(OK), "--routes", str(ROUTES), "--out", str(out)]) == 0
    written = out / "catalogue.json"
    assert written.is_file() and (out / "routes.json").is_file()
    cat = CatalogueFile.model_validate_json(written.read_text(encoding="utf-8"))
    assert [e.soc2020 for e in cat.entries] == ["2451", "2134", "2433"]

    data = load_data(snapshot_dir=out)
    assert data.careers["2451"].title == "Architect"
    assert data.careers["2134"].title == "Software developer"
    assert data.careers["2451"].metrics["shortage"].is_missing


def test_cli_bad_csv_exits_non_zero(tmp_path, capsys):
    out = tmp_path / "snap"
    assert main(["--curated", str(BAD), "--routes", str(ROUTES), "--out", str(out)]) != 0
    assert "line 2 (soc2020 2451)" in capsys.readouterr().out
    assert not (out / "catalogue.json").exists() and not (out / "routes.json").exists()
