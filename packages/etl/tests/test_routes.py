"""Routes ETL: curated routes CSV -> RoutesFile -> snapshots/routes.json."""
from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest

from avenir_contracts import vocab
from avenir_contracts.catalogue import RoutesFile
from avenir_contracts.data import load_data
from avenir_etl.build import main
from avenir_etl.curated import CuratedError, load_curated
from avenir_etl.routes import load_routes

FIX = Path(__file__).parent / "fixtures"
OK = FIX / "routes_ok.csv"
BAD = FIX / "routes_bad.csv"
OCC_OK = FIX / "occupations_ok.csv"
OCC_BAD = FIX / "occupations_bad.csv"
REAL_ROUTES = Path(__file__).parents[3] / "data" / "curated" / "routes.csv"
SOCS = {"2451", "2134", "2433", "3544"}
HEADER = "soc2020,nation,kind,name,provider,entry_requirements,url,source,verified_by\n"


def test_load_routes_ok_keeps_every_field_and_round_trips():
    rf = load_routes(OK, SOCS, generated_at="2026-10-17T00:00:00+00:00")
    assert rf.status == "preliminary" and rf.generated_at == "2026-10-17T00:00:00+00:00"
    assert [(r.soc2020, r.nation, r.kind) for r in rf.routes] == [
        ("2451", "scotland", "degree"),
        ("2451", "england", "degree"),
        ("2134", "scotland", "graduate_apprenticeship"),
    ]
    assert rf.routes[0].provider == "TEST"
    assert rf.routes[2].provider is None  # empty provider cell
    assert rf.routes[2].entry_requirements == "TEST entry requirements, with a comma (test data)"
    assert all(r.verified_by == "test" and r.url.startswith("https://") for r in rf.routes)
    assert RoutesFile.model_validate_json(rf.model_dump_json()) == rf


def test_generated_at_defaults_to_now():
    assert load_routes(OK, SOCS).generated_at


def test_england_route_stays_england_after_load_data(tmp_path):
    out = tmp_path / "snap"
    assert main(["--curated", str(OCC_OK), "--routes", str(OK), "--out", str(out)]) == 0
    routes = load_data(snapshot_dir=out).routes
    assert {r.nation for r in routes["2451"]} == {"scotland", "england"}
    assert {r.nation: r.kind for r in routes["2451"]}["england"] == "degree"
    assert [r.nation for r in routes["2134"]] == ["scotland"]


def test_load_routes_bad_names_every_bad_row_and_not_the_good_one():
    with pytest.raises(CuratedError) as exc:
        load_routes(BAD, {"2451", "2134"})
    msg = str(exc.value)
    assert isinstance(exc.value, ValueError)
    assert "line 2 (soc2020 2451)" in msg and "verified_by" in msg
    assert "line 3 (soc2020 9999)" in msg and "demo set" in msg
    assert "line 4 (soc2020 2451)" in msg and "mars" in msg
    assert "line 5 (soc2020 2451)" in msg and "bootcamp" in msg
    assert "line 7 (soc2020 2451)" in msg and "name is empty" in msg
    assert "line 8 (soc2020 2451)" in msg and "entry_requirements is empty" in msg
    assert "line 9 (soc2020 2451)" in msg and "url is empty" in msg
    assert "line 10 (soc2020 2451)" in msg and "source is empty" in msg
    assert "line 11 (soc2020 2451)" in msg and "https://" in msg
    assert "line 12 (soc2020 2134)" in msg and "duplicate" in msg
    assert "line 6" not in msg  # the one good row


def test_error_messages_list_allowed_values_from_vocab():
    with pytest.raises(CuratedError) as exc:
        load_routes(BAD, {"2451", "2134"})
    msg = str(exc.value)
    for v in (*get_args(vocab.Nation), *get_args(vocab.RouteKind)):
        assert v in msg


def test_same_route_in_two_nations_or_kinds_is_not_a_duplicate(tmp_path):
    f = tmp_path / "routes.csv"
    f.write_text(
        HEADER
        + "2451,scotland,degree,TEST a,,r,https://example.org/t,s,test\n"
        + "2451,england,degree,TEST a,,r,https://example.org/t,s,test\n"
        + "2451,scotland,college,TEST a,,r,https://example.org/t,s,test\n",
        encoding="utf-8",
    )
    assert len(load_routes(f, SOCS).routes) == 3


def test_header_only_file_is_an_empty_routes_file(tmp_path):
    f = tmp_path / "routes.csv"
    f.write_text(HEADER, encoding="utf-8")
    rf = load_routes(f, SOCS)
    assert rf.routes == [] and rf.status == "preliminary"
    assert load_routes(REAL_ROUTES, SOCS).routes == []  # the committed file ships header-only


def test_missing_column_names_it(tmp_path):
    f = tmp_path / "routes.csv"
    f.write_text("soc2020,nation,kind,name,provider,url,source\n2451,scotland,degree,x,,u,s\n", encoding="utf-8")
    with pytest.raises(CuratedError) as exc:
        load_routes(f, SOCS)
    assert "entry_requirements" in str(exc.value) and "verified_by" in str(exc.value)


def test_cli_writes_both_files(tmp_path, capsys):
    out = tmp_path / "snap"
    assert main(["--curated", str(OCC_OK), "--routes", str(OK), "--out", str(out)]) == 0
    assert (out / "catalogue.json").is_file()
    rf = RoutesFile.model_validate_json((out / "routes.json").read_text(encoding="utf-8"))
    assert len(rf.routes) == 3
    assert "no rows yet" not in capsys.readouterr().err


def test_cli_empty_routes_warns_but_still_writes(tmp_path, capsys):
    empty = tmp_path / "routes.csv"
    empty.write_text(HEADER, encoding="utf-8")
    out = tmp_path / "snap"
    assert main(["--curated", str(OCC_OK), "--routes", str(empty), "--out", str(out)]) == 0
    assert "routes.csv has no rows yet; roadmap will show routes as missing" in capsys.readouterr().err
    assert RoutesFile.model_validate_json((out / "routes.json").read_text(encoding="utf-8")).routes == []


def test_cli_bad_routes_leaves_no_partial_output(tmp_path, capsys):
    out = tmp_path / "snap"
    assert main(["--curated", str(OCC_OK), "--routes", str(BAD), "--out", str(out)]) != 0
    assert "line 2 (soc2020 2451)" in capsys.readouterr().out
    assert not (out / "catalogue.json").exists() and not (out / "routes.json").exists()


def test_cli_reports_errors_from_both_inputs(tmp_path, capsys):
    out = tmp_path / "snap"
    assert main(["--curated", str(OCC_BAD), "--routes", str(BAD), "--out", str(out)]) != 0
    printed = capsys.readouterr().out
    assert "astrology" in printed and "bootcamp" in printed
    assert not out.exists() or not any(out.iterdir())


def test_load_curated_zero_rows_is_an_error(tmp_path):
    f = tmp_path / "occupations.csv"
    f.write_text("soc2020,title,aliases,description,entry_subjects,verified_by\n", encoding="utf-8")
    with pytest.raises(CuratedError, match="no data rows"):
        load_curated(f, SOCS)


def test_load_curated_missing_columns_named(tmp_path):
    f = tmp_path / "occupations.csv"
    f.write_text("soc2020,title,aliases\n2451,Architect,\n", encoding="utf-8")
    with pytest.raises(CuratedError) as exc:
        load_curated(f, SOCS)
    msg = str(exc.value)
    assert all(c in msg for c in ("description", "entry_subjects", "verified_by"))


def test_cli_explicit_missing_oid_warns_on_stderr(tmp_path, capsys):
    out = tmp_path / "snap"
    missing = tmp_path / "nope.xlsx"
    assert main(["--curated", str(OCC_OK), "--routes", str(OK), "--oid", str(missing), "--out", str(out)]) == 0
    assert str(missing) in capsys.readouterr().err
    cat = (out / "catalogue.json").read_text(encoding="utf-8")
    assert "not loaded" in cat  # shortage still missing


def test_cli_without_oid_does_not_warn(tmp_path, capsys):
    main(["--curated", str(OCC_OK), "--routes", str(OK), "--out", str(tmp_path / "snap")])
    assert "oid" not in capsys.readouterr().err.lower()
