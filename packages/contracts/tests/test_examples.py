"""The frontend handoff pack (docs/frontend/) is generated; these tests keep it honest."""
import json
import re

import jsonschema
import pytest
from pydantic import TypeAdapter

from avenir_contracts import (
    BacktestOut,
    Career,
    Crisis,
    HedgeCandidate,
    HistoryPoint,
    Route,
    SourceInfo,
    SourceStatus,
    Tag,
    load_data,
)
from avenir_contracts import examples as ex
from avenir_contracts.data import REPO_ROOT
from avenir_contracts.envelope import Envelope

COMMITTED = REPO_ROOT / "docs" / "frontend"
SUBDIRS = ("schemas", "examples")


def _files(root, normalise=False):
    """{relative path: bytes} for the generated files. `normalise` turns CRLF into LF (committed side only)."""
    paths = [p for d in SUBDIRS for p in (root / d).glob("*.json")] + [root / ex.MANIFEST]
    out = {p.relative_to(root).as_posix(): p.read_bytes() for p in paths}
    return {k: v.replace(b"\r\n", b"\n") for k, v in out.items()} if normalise else out


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    out = tmp_path_factory.mktemp("frontend")
    ex.write(out)
    return out


def test_generation_is_byte_identical(generated, tmp_path):
    ex.write(tmp_path)
    assert _files(tmp_path) == _files(generated)


def test_expected_files_exist(generated):
    names = set(_files(generated))
    assert {f"schemas/{m}.json" for m in ex.SCHEMA_MODELS} <= names
    for f in ("career_2451", "careers", "tags", "history_2451", "hedge_candidates_2451", "routes_2451", "crises",
              "backtest_years", "sources", "envelope_career_2451", "error_404", "flags"):
        assert f"examples/{f}.json" in names
    assert any(n.startswith("examples/backtest_2") for n in names)


def test_files_are_sorted_indented_with_trailing_newline(generated):
    for name, raw in _files(generated).items():
        text = raw.decode("utf-8")
        assert text.endswith("}\n") or text.endswith("]\n"), name
        assert text == json.dumps(json.loads(text), indent=2, sort_keys=True, ensure_ascii=False) + "\n", name


def test_committed_pack_is_not_stale(generated):
    # normalise: a Windows checkout with core.autocrlf=true turns LF into CRLF on disk
    assert _files(COMMITTED, normalise=True) == _files(generated), "run: python -m avenir_contracts.examples"


def test_crlf_checkout_still_compares_equal(generated, tmp_path):
    crlf = tmp_path / "crlf"
    for rel, raw in _files(generated).items():
        (crlf / rel).parent.mkdir(parents=True, exist_ok=True)
        (crlf / rel).write_bytes(raw.replace(b"\n", b"\r\n"))
    assert _files(crlf) != _files(generated)
    assert _files(crlf, normalise=True) == _files(generated)


def test_rerun_removes_only_files_it_generated(tmp_path):
    ex.write(tmp_path)
    (tmp_path / "README.md").write_text("mine")
    (tmp_path / "examples" / "hand_made.json").write_text("{}")
    stale = tmp_path / "examples" / "career_0000.json"
    stale.write_text("{}")
    manifest = json.loads((tmp_path / ex.MANIFEST).read_text())
    manifest["files"].append("examples/career_0000.json")
    (tmp_path / ex.MANIFEST).write_text(json.dumps(manifest))
    ex.write(tmp_path)
    assert not stale.exists()
    assert (tmp_path / "README.md").exists() and (tmp_path / "examples" / "hand_made.json").exists()


def _load(root, name):
    return json.loads((root / "examples" / f"{name}.json").read_text(encoding="utf-8"))


def _schema(root, model):
    return json.loads((root / "schemas" / f"{model}.json").read_text(encoding="utf-8"))


def _check(root, name, model, many=False):
    raw = _load(root, name)
    items = raw if many else [raw]
    schema = _schema(root, model.__name__)
    for item in items:
        model.model_validate(item)
        jsonschema.validate(item, schema)


def test_examples_validate_against_models_and_schemas(generated):
    _check(generated, "career_2451", Career)
    _check(generated, "tags", Tag, many=True)
    _check(generated, "history_2451", HistoryPoint, many=True)
    _check(generated, "hedge_candidates_2451", HedgeCandidate, many=True)
    _check(generated, "routes_2451", Route, many=True)
    _check(generated, "crises", Crisis, many=True)
    year = _load(generated, "backtest_years")[0]
    _check(generated, f"backtest_{year}", BacktestOut)
    src = _load(generated, "sources")
    assert set(src) == {"statuses", "registry"}
    for s in src["statuses"]:
        SourceStatus.model_validate(s)
        jsonschema.validate(s, _schema(generated, "SourceStatus"))
    for info in src["registry"].values():
        SourceInfo.model_validate(info)


def test_careers_and_years(generated):
    data = load_data()
    careers = _load(generated, "careers")
    assert [c["soc2020"] for c in careers] == sorted(data.careers)
    assert all(set(c) == {"soc2020", "title"} for c in careers)
    assert _load(generated, "backtest_years") == sorted(data.backtest)


def test_envelopes(generated):
    ok = TypeAdapter(Envelope[Career]).validate_python(_load(generated, "envelope_career_2451"))
    assert ok.ok and ok.error is None and ok.meta.request_id == "example"
    assert ok.meta.as_of and "T" in ok.meta.as_of  # from the data, not now()
    err = Envelope.model_validate(_load(generated, "error_404"))
    assert not err.ok and err.data is None
    assert err.error.code == "NOT_FOUND" and err.error.message == "Unknown SOC code 9999"


def test_flags_example_matches_ml(generated):
    from pathfinder_ml import FLAG_TEXT, MUST_MENTION

    flags = _load(generated, "flags")
    assert set(flags) == set(FLAG_TEXT)
    for k, v in flags.items():
        assert v == {"text": FLAG_TEXT[k], "must_mention": k in MUST_MENTION}


SECRET = re.compile(
    r'"[^"]*(secret|token|password|api_?key|app_?key|app_?id)[^"]*"\s*:'   # a JSON key that looks like a credential
    r"|sk-[A-Za-z0-9]{8,}|bearer\s+[A-Za-z0-9._-]{8,}",                    # a value that looks like a key
    re.I,
)


def test_secret_pattern_catches_keys_but_not_words():
    assert SECRET.search('{"api_key": "x"}') and SECRET.search("sk-abcdefgh1234") and SECRET.search("Bearer abcdefgh12")
    assert not SECRET.search('{"note": "tokens and secretaries are words"}')


def _walk(node):
    yield node
    for child in node.values() if isinstance(node, dict) else node if isinstance(node, list) else []:
        yield from _walk(child)


def test_no_secrets_and_example_org_only_in_mock_objects(generated):
    for name, raw in _files(generated).items():
        assert not SECRET.search(raw.decode("utf-8")), name
        if not name.startswith("examples/"):
            continue
        for node in _walk(json.loads(raw)):
            if isinstance(node, dict) and any(isinstance(v, str) and "example.org" in v for v in node.values()):
                assert node.get("source") == "MOCK", (name, node)
