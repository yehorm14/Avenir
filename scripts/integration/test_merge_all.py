"""Exercise the harness against local Git repositories; no network or team refs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from merge_all import Config, compatibility_issues, execute, failure_owner, parse_pytest, remove_temp, render_report, run_checks


def git(root, *args):
    return subprocess.run(
        ["git", "-c", "user.name=codex", "-c", "user.email=codex@localhost", *args],
        cwd=root, check=True, text=True, capture_output=True,
    ).stdout.strip()


def commit(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")
    git(root, "add", path)
    git(root, "commit", "-m", "test fixture")


@pytest.fixture
def repositories(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", str(remote))
    seed = tmp_path / "seed"
    git(tmp_path, "init", "-b", "main", str(seed))
    commit(seed, "shared.txt", "base\n")
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "origin", "main")
    repo = tmp_path / "checkout"
    git(tmp_path, "clone", "-b", "main", str(remote), str(repo))
    return seed, repo


def branch(seed, name, path, value):
    git(seed, "checkout", "-B", name, "main")
    commit(seed, path, value)
    git(seed, "push", "origin", name)


def config(tmp_path, repo, **kwargs):
    return Config(repo=repo, temp=tmp_path / "codex-integration-tmp", report_dir=tmp_path / "reports", **kwargs)


def fake_checks(tree, label, report_dir):
    assert subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=tree, capture_output=True).returncode == 1
    return {"label": label, "pytest": {"code": 0, "summary": "1 passed", "failures": []},
            "lint": {"code": 0, "summary": "clean", "failures": []}, "probe": {}}


def test_merges_in_order_aborts_conflict_and_continues(tmp_path, repositories):
    seed, repo = repositories
    branch(seed, "nazar/decision", "shared.txt", "decision\n")
    branch(seed, "nazar/api", "shared.txt", "api\n")
    branch(seed, "yehor/catalogue", "catalogue.txt", "catalogue\n")
    branch(seed, "arsenii/evidence", "ml.txt", "evidence\n")
    original = git(repo, "rev-parse", "HEAD")
    cfg = config(tmp_path, repo)
    result = execute(cfg, check_runner=fake_checks)
    statuses = {r["branch"]: r for r in result["branches"]}
    assert statuses["origin/nazar/decision"]["status"] == "merged"
    assert statuses["origin/nazar/api"]["status"] == "conflict"
    assert statuses["origin/nazar/api"]["files"] == ["shared.txt"]
    assert statuses["origin/yehor/catalogue"]["status"] == "merged"
    assert statuses["origin/arsenii/evidence"]["status"] == "merged"
    assert statuses["origin/yehor/live-adapters"]["status"] == "missing"
    assert git(repo, "rev-parse", "HEAD") == original
    assert git(repo, "status", "--porcelain") == ""
    assert not cfg.temp.exists()
    assert list(cfg.report_dir.glob("integration-report-*.md"))
    assert "shared.txt" in Path(result["report"]).read_text()
    assert Path(cfg.report_dir / "codex-status.md").read_text().startswith("# Codex integration status")


def test_overlay_replaces_only_ml_and_compares_freeze(tmp_path, repositories):
    seed, repo = repositories
    commit(seed, "packages/ml/obsolete.txt", "old")
    git(seed, "push", "origin", "main")
    overlay = tmp_path / "overlay"
    git(tmp_path, "init", "-b", "main", str(overlay))
    commit(overlay, "packages/ml/new.txt", "new")
    commit(overlay, "snapshots/ml/occupations.json", json.dumps({"occupations": []}))
    seen = []

    def check(tree, label, directory):
        seen.append(label)
        if label != "baseline":
            assert not (tree / "packages/ml/obsolete.txt").exists()
            assert (tree / "packages/ml/new.txt").read_text() == "new"
            assert (tree / "shared.txt").read_text() == "base\n"
            assert git(tree, "status", "--porcelain")  # overlay never committed
        return fake_checks(tree, label, directory)

    cfg = config(tmp_path, repo, branches=[], overlay_ml="main", ml_repo=overlay)
    result = execute(cfg, check_runner=check)
    assert seen == ["baseline", "overlay", "freeze"]
    assert result["overlay_sha"] == git(overlay, "rev-parse", "main")
    assert "ML v1.1 compatibility" in Path(result["report"]).read_text()
    assert not cfg.temp.exists()


def test_stale_detached_worktree_is_removed(tmp_path, repositories):
    _, repo = repositories
    cfg = config(tmp_path, repo, branches=[])
    git(repo, "worktree", "add", "--detach", str(cfg.temp), "origin/main")
    (cfg.temp / "leftover.txt").write_text("discard temporary output")
    execute(cfg, check_runner=fake_checks)
    assert not cfg.temp.exists()


@pytest.mark.parametrize("registered", [False, True])
def test_refuses_to_remove_unowned_or_attached_directory(tmp_path, repositories, registered):
    _, repo = repositories
    cfg = config(tmp_path, repo)
    if registered:
        git(repo, "worktree", "add", "-b", "do-not-remove", str(cfg.temp), "origin/main")
    else:
        cfg.temp.mkdir()
        (cfg.temp / "keep.txt").write_text("keep")
    with pytest.raises(RuntimeError, match="[Rr]efus"):
        remove_temp(cfg)
    assert cfg.temp.exists()


def test_cleanup_and_report_after_check_runner_error(tmp_path, repositories):
    _, repo = repositories
    cfg = config(tmp_path, repo, branches=[])

    def broken(*args):
        raise RuntimeError("fixture error")

    result = execute(cfg, check_runner=broken)
    assert result["errors"]
    assert not cfg.temp.exists()
    assert Path(result["report"]).is_file()


def test_lock_protects_same_temp_across_different_report_directories(tmp_path, repositories):
    _, repo = repositories
    cfg = config(tmp_path, repo, branches=[])
    lock = cfg.temp.parent / ".codex-integration.lock"
    lock.write_text("active run")
    with pytest.raises(RuntimeError, match="locked"):
        execute(cfg, check_runner=fake_checks)
    assert lock.read_text() == "active run"


def test_runs_real_pytest_and_ruff_from_tree(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "test_sample.py").write_text("def test_good():\n    assert True\n\ndef test_bad():\n    assert False\n")
    cfg = Config(temp=tree, python=sys.executable)
    result = run_checks(cfg, "baseline", tmp_path)
    assert result["pytest"]["summary"].startswith("1 passed, 1 failed")
    assert result["pytest"]["failures"] == ["test_sample.py::test_bad"]
    assert result["lint"]["code"] == 0


def test_report_attributes_unknown_metric_to_contract_owner():
    run = fake_checks_result([])
    run["probe"] = {"unknown_metric_keys": ["future_metric"]}
    report = render_report({"time": "2026-10-17 23:30 BST", "base_sha": "abc", "branches": [],
                            "overlay": None, "runs": [dict(run, label="baseline")], "errors": [], "cleanup": "removed"})
    assert "### Yehor" in report
    assert "future_metric" in report


def test_probe_problems_are_reported_as_integration_failures():
    assert compatibility_issues({}) == []  # injected checks may omit the optional probe
    assert compatibility_issues({"imports_from_temp_tree": False})[0][0] == "Codex"
    assert compatibility_issues({"join_metric_flag_losses": ["test"]})[0][0] == "Yehor"
    assert compatibility_issues({"sizes": {"snapshots/ml/test.json": 5_000_001}})[0][0] == "Arsenii"


def test_pytest_junit_preserves_parameterized_ids_and_collection_errors(tmp_path):
    xml = tmp_path / "results.xml"
    xml.write_text('''<testsuites><testsuite tests="3" failures="1" errors="1" skipped="0">
      <testcase classname="packages.decision.tests.test_picks" name="test_picks[real]">
        <failure message="assertion">AssertionError</failure></testcase>
      <testcase classname="" name="packages/contracts/tests/test_models.py"><error>ImportError</error></testcase>
      <testcase classname="packages.ml.tests.test_contract" name="test_ok"/>
    </testsuite></testsuites>''')
    result = parse_pytest(1, "", xml)
    assert result["failures"] == ["packages/contracts/tests/test_models.py",
                                  "packages/decision/tests/test_picks.py::test_picks[real]"]
    assert "1 failed" in result["summary"]
    assert "1 error" in result["summary"]


def test_missing_junit_is_an_explicit_execution_failure(tmp_path):
    result = parse_pytest(4, "", tmp_path / "absent.xml")
    assert result["code"] == 4
    assert "unavailable" in result["summary"]


@pytest.mark.parametrize(("path", "owner"), [
    ("packages/decision/tests/test_picks.py::test_a", "Nazar"),
    ("services/api/tests/test_api.py", "Nazar"),
    ("packages/contracts/tests/test_data.py", "Yehor"),
    ("packages/adapters/tests/test_live.py", "Yehor"),
    ("packages/etl/tests/test_catalogue.py", "Yehor"),
    ("scripts/fetch/ons.py", "Yehor"),
    ("snapshots/ml/occupations.json", "Arsenii"),
    ("packages/ml/tests/test_contract.py", "Arsenii"),
    ("scripts/integration/merge_all.py", "Codex"),
])
def test_ownership(path, owner):
    assert failure_owner(path) == owner


def test_report_differentiates_overlay_and_freeze_failures():
    base = fake_checks_result(["packages/contracts/tests/test_old.py::test_a"])
    overlay = fake_checks_result(["packages/contracts/tests/test_old.py::test_a", "services/api/tests/test_real.py::test_b"])
    freeze = fake_checks_result(["services/api/tests/test_freeze.py::test_c"])
    report = render_report({"time": "2026-10-17 23:30 BST", "base_sha": "abc", "branches": [],
                            "overlay": "main", "overlay_sha": "def", "runs": [
                                dict(base, label="baseline"), dict(overlay, label="overlay"), dict(freeze, label="freeze")],
                            "errors": [], "cleanup": "removed"})
    assert "Only with overlay" in report
    assert "services/api/tests/test_real.py::test_b" in report
    assert "Nazar" in report
    assert "Likely cause" in report
    assert "services/api/tests/test_freeze.py::test_c" in report


def fake_checks_result(failures):
    return {"pytest": {"code": bool(failures), "summary": "fixture summary", "failures": failures},
            "lint": {"code": 0, "summary": "clean", "failures": []}, "probe": {}}
