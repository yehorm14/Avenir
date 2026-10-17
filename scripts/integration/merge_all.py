"""Throwaway integration merges and ML compatibility reports (stdlib only).

Run with the project's Python environment. Nothing is pushed or committed outside
the detached temporary worktree. See README.md beside this file for report semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

DEFAULT_BRANCHES = (
    "origin/nazar/decision", "origin/nazar/api", "origin/yehor/catalogue",
    "origin/yehor/live-adapters", "origin/yehor/contract-v1.1",
)
TEMP_NAME = "codex-integration-tmp"


@dataclass
class Config:
    repo: Path = Path("C:/dev/Avenir")
    temp: Path = Path("C:/dev/Avenir-wt") / TEMP_NAME
    report_dir: Path = Path("C:/dev/Avenir-wt/_shared")
    ml_repo: Path = Path("C:/dev/KATYATA")
    branches: list[str] | None = None
    overlay_ml: str | None = None
    python: str = sys.executable
    timeout: int = 600


def command(args, cwd, *, env=None, timeout=120):
    # Prevent inherited Git overrides from redirecting a command into another tree.
    clean = {k: v for k, v in (os.environ if env is None else env).items() if not k.startswith("GIT_")}
    return subprocess.run(args, cwd=cwd, env=clean, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def git(repo, *args, check=True):
    result = command(["git", *args], repo)
    if check and result.returncode:
        # Do not copy Git output: it can contain credential URLs or machine names.
        raise RuntimeError(f"git {args[0]} failed (exit {result.returncode})")
    return result


def london_now():
    """UK civil time without depending on an installed Windows tzdata package."""
    now = datetime.now(UTC)

    def last_sunday(month):
        start = datetime(now.year, month + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)
        return start - timedelta(days=(start.weekday() + 1) % 7)

    summer = last_sunday(3) <= now < last_sunday(10)
    return now.astimezone(timezone(timedelta(hours=int(summer)), "BST" if summer else "GMT"))


def validate_temp(cfg):
    repo, temp = cfg.repo.resolve(), cfg.temp.resolve()
    if temp.name != TEMP_NAME or repo == temp or repo in temp.parents or temp in repo.parents:
        raise RuntimeError("Refusing unsafe temporary worktree path")
    if cfg.temp.is_symlink() or cfg.temp.is_junction():
        raise RuntimeError("Refusing temporary worktree link")


def worktrees(repo):
    records = []
    current = {}
    for item in git(repo, "worktree", "list", "--porcelain", "-z").stdout.split("\0"):
        if not item:
            if current:
                records.append(current)
                current = {}
        else:
            key, _, value = item.partition(" ")
            current[key] = value
    if current:
        records.append(current)
    return records


def remove_temp(cfg):
    """Only remove the exact registered, detached, disposable worktree."""
    validate_temp(cfg)
    record = next((r for r in worktrees(cfg.repo) if Path(r["worktree"]).resolve() == cfg.temp.resolve()), None)
    if record is None:
        if cfg.temp.exists():
            raise RuntimeError("Refusing to remove unregistered temporary directory")
        return
    if "detached" not in record or "locked" in record:
        raise RuntimeError("Refusing to remove attached or locked temporary worktree")
    git(cfg.repo, "worktree", "remove", "--force", str(cfg.temp.resolve()))


def merge_branches(cfg):
    refs = git(cfg.repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/").stdout.splitlines()
    selected = list(DEFAULT_BRANCHES) if cfg.branches is None else list(cfg.branches)
    if cfg.branches is None:
        selected.extend(sorted(r for r in refs if r.startswith("origin/arsenii/")))
    records = []
    for ref in dict.fromkeys(selected):
        record = {"branch": ref, "sha": None, "status": "missing", "files": []}
        records.append(record)
        if ref not in refs:
            continue
        sha = git(cfg.repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.strip()
        record["sha"] = sha
        result = git(cfg.temp, "-c", "user.name=codex", "-c", "user.email=codex@localhost",
                     "-c", "commit.gpgsign=false", "-c", "core.hooksPath=",
                     "merge", "--no-edit", "--no-gpg-sign", sha, check=False)
        if result.returncode == 0:
            record["status"] = "merged"
            continue
        record["files"] = git(cfg.temp, "diff", "--name-only", "--diff-filter=U").stdout.splitlines()
        record["status"] = "conflict" if record["files"] else "error"
        merging = git(cfg.temp, "rev-parse", "--verify", "MERGE_HEAD", check=False)
        if merging.returncode == 0:
            git(cfg.temp, "merge", "--abort")
        if git(cfg.temp, "status", "--porcelain").stdout.strip():
            raise RuntimeError("Merge did not return the temporary tree to a clean state")
    return records


def overlay_ml(cfg):
    sha = git(cfg.ml_repo, "rev-parse", "--verify", f"{cfg.overlay_ml}^{{commit}}").stdout.strip()
    # Validate the complete archive before replacing anything. Reject links and traversal.
    with tempfile.TemporaryFile() as archive:
        result = subprocess.run(["git", "-C", str(cfg.ml_repo), "archive", sha, "packages/ml", "snapshots/ml"],
                                stdout=archive, stderr=subprocess.PIPE, timeout=120)
        if result.returncode:
            raise RuntimeError(f"ML archive failed (exit {result.returncode})")
        archive.seek(0)
        with tarfile.open(fileobj=archive) as tar:
            members = tar.getmembers()
            roots = ("packages/ml", "snapshots/ml")
            for member in members:
                name = member.name.rstrip("/")
                if name in ("packages", "snapshots") and member.isdir():
                    continue
                target = (cfg.temp / name).resolve()
                allowed = any(name == root or name.startswith(root + "/") for root in roots)
                if not allowed or not target.is_relative_to(cfg.temp.resolve()) or not (member.isfile() or member.isdir()):
                    raise RuntimeError("Refusing unsafe ML archive member")
            if not all(any(m.isfile() and m.name.startswith(root + "/") for m in members) for root in roots):
                raise RuntimeError("ML archive must include both packages/ml and snapshots/ml")
            for root in roots:
                target = (cfg.temp / root).resolve()
                if target.exists():
                    if not target.is_relative_to(cfg.temp.resolve()):
                        raise RuntimeError("Refusing unsafe ML replacement path")
                    shutil.rmtree(target)
            tar.extractall(cfg.temp, members=members, filter="data")
    return sha


def failure_owner(path):
    path = path.replace("\\", "/")
    groups = {
        "Nazar": ("packages/decision/", "services/api/", "docker-compose.yml", "docs/openapi.json"),
        "Yehor": ("packages/contracts/", "packages/adapters/", "packages/etl/", "scripts/fetch/", "data/"),
        "Arsenii": ("packages/ml/", "snapshots/ml/"),
        "Codex": ("scripts/integration/", "context/codex-integration.md"),
        "TBD (frontend/glue)": ("apps/web/", "README"),
    }
    return next((owner for owner, prefixes in groups.items() if path.startswith(prefixes)), "Unassigned")


def junit_id(case):
    name = case.get("name", "")
    classname = case.get("classname", "")
    if not classname:
        return name.replace("\\", "/")
    # pytest's JUnit output encodes the module and optional test class with dots.
    parts = classname.split(".")
    test_index = next((i for i, part in enumerate(parts) if part.startswith("test_")), len(parts) - 1)
    module = "/".join(parts[:test_index + 1]) + ".py"
    return "::".join([module, *parts[test_index + 1:], name])


def parse_pytest(code, output, xml_path):
    result = {"code": code, "summary": f"exit {code}; JUnit unavailable", "failures": []}
    if not xml_path.is_file():
        return result
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return result
    cases = list(root.iter("testcase"))
    failed = [c for c in cases if c.find("failure") is not None]
    errors = [c for c in cases if c.find("error") is not None]
    skipped = [c for c in cases if c.find("skipped") is not None]
    passed = len(cases) - len(failed) - len(errors) - len(skipped)
    result["summary"] = f"{passed} passed, {len(failed)} failed, {len(errors)} errors, {len(skipped)} skipped (exit {code})"
    result["failures"] = sorted({junit_id(c) for c in [*failed, *errors]})
    return result


def check_environment(tree, freeze=False):
    env = {k: v for k, v in os.environ.items()
           if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", k, re.I)}
    for key in ("PATHFINDER_ML_DIR", "AVENIR_SNAPSHOT_DIR", "AVENIR_FREEZE", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(key, None)
    # Explicit paths prevent the primary checkout's editable install winning in probes.
    folders = ("packages/ml", "packages/contracts", "packages/decision", "packages/adapters", "packages/etl", "services/api")
    env["PYTHONPATH"] = os.pathsep.join(str(tree / folder) for folder in folders)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if freeze:
        env["AVENIR_FREEZE"] = "1"
    return env


def run_checks(cfg, label, artifacts):
    env = check_environment(cfg.temp, freeze=label == "freeze")
    xml = artifacts / f"{label}.xml"
    result = command([cfg.python, "-m", "pytest", "-q", f"--junitxml={xml}", "-o", "junit_family=xunit1"],
                     cfg.temp, env=env, timeout=cfg.timeout)
    tests = parse_pytest(result.returncode, result.stdout, xml)
    lint = {"code": 0, "summary": "not repeated in freeze mode (same files)", "failures": []}
    if label != "freeze":
        result = command([cfg.python, "-m", "ruff", "check", ".", "--output-format=json"],
                         cfg.temp, env=env, timeout=cfg.timeout)
        try:
            diagnostics = json.loads(result.stdout)
            failures = sorted({f"{Path(d['filename']).relative_to(cfg.temp).as_posix()}:{d['location']['row']} {d['code']}"
                               for d in diagnostics})
            lint = {"code": result.returncode, "summary": f"{len(diagnostics)} diagnostics (exit {result.returncode})",
                    "failures": failures}
        except (ValueError, TypeError, KeyError):
            lint = {"code": result.returncode or 1, "summary": "ruff output unavailable", "failures": []}
    probe = command([cfg.python, str(Path(__file__).with_name("ml_probe.py"))], cfg.temp, env=env, timeout=cfg.timeout)
    try:
        evidence = json.loads(probe.stdout)
    except ValueError:
        evidence = {"error": f"probe unavailable (exit {probe.returncode})"}
    return {"label": label, "pytest": tests, "lint": lint, "probe": evidence}


def likely_cause(owner):
    return {
        "Nazar": "check real-data fixture assumptions and decision/API expectations; ML() prefers real artefacts over mocks.",
        "Yehor": ("check contract vocabulary, pass-through fields, history ranges and mock fixture expectations "
                  "against the ML version."),
        "Arsenii": "check artefact shape and ML loader/contract tests against real evidence rather than mock-only assumptions.",
        "Codex": "check harness orchestration and temporary repository assumptions.",
    }.get(owner, "inspect the owning test or lint rule; no cause established automatically.")


def compatibility_issues(probe):
    issues = []
    if probe.get("unknown_metric_keys"):
        issues.append(("Yehor", f"packages/contracts: unknown ML metric keys `{', '.join(probe['unknown_metric_keys'])}`"))
    if probe.get("load_data_ok") is False:
        issues.append(("Yehor", "packages/contracts: ML load probe failed (see evidence below)"))
    if probe.get("join_metric_flag_losses") or probe.get("load_data_metric_flag_losses"):
        issues.append(("Yehor", "packages/contracts: metric flags lost in the join/load probe"))
    if probe.get("imports_from_temp_tree") is False or ("error" in probe and "load_data_ok" not in probe):
        issues.append(("Codex", "scripts/integration: probe unavailable or imports resolved outside the temporary tree"))
    for path, size in probe.get("sizes", {}).items():
        if size > 5_000_000:
            issues.append(("Arsenii", f"`{path}` exceeds the requested 5 MB threshold"))
    return issues


def probe_lines(probe):
    if not probe:
        return ["- Probe not supplied."]
    lines = []
    for key, value in probe.items():
        if key == "sizes":
            lines += ["- Snapshot sizes (bytes; >5 MB means >5,000,000 bytes):"]
            lines += [f"  - `{name}`: {size:,}" + (" **OVER 5 MB**" if size > 5_000_000 else "")
                      for name, size in value.items()]
        else:
            lines.append(f"- {key}: `{json.dumps(value, ensure_ascii=True)}`")
    return lines


def render_report(report):
    lines = ["# Integration report", "", f"Time: {report['time']}", f"Base origin/main: `{report['base_sha']}`",
             f"Overlay: `{report['overlay'] or 'none'}`; resolved SHA: `{report.get('overlay_sha') or 'none'}`", "",
             "## Branches", "", "| Branch | SHA | Result | Conflicting files |", "| --- | --- | --- | --- |"]
    for b in report["branches"]:
        lines.append(f"| {b['branch']} | {b['sha'] or 'unavailable'} | {b['status']} | {', '.join(b['files']) or 'none'} |")
    lines += ["", "## Checks", ""]
    groups = {}
    for run in report["runs"]:
        lines += [f"### {run['label']}", "", f"- Tests: {run['pytest']['summary']}", f"- Lint: {run['lint']['summary']}"]
        for check in ("pytest", "lint"):
            for failure in run[check]["failures"]:
                groups.setdefault(failure_owner(failure), []).append(f"{run['label']} {check}: `{failure}`")
        for owner, message in compatibility_issues(run.get("probe", {})):
            groups.setdefault(owner, []).append(f"{run['label']} {message}")
    for b in report["branches"]:
        for path in b["files"]:
            groups.setdefault(failure_owner(path), []).append(f"merge conflict ({b['branch']}): `{path}`")
    lines += ["", "## Failures by owner", ""]
    if not groups:
        lines.append("No test IDs, lint diagnostics or merge-conflict files reported. Check execution errors below.")
    for owner, failures in sorted(groups.items()):
        lines += [f"### {owner}", "", *[f"- {f}" for f in failures], f"- Likely cause (inference): {likely_cause(owner)}", ""]
    lines += ["", "## ML v1.1 compatibility", ""]
    runs = {r["label"]: r for r in report["runs"]}
    if "baseline" in runs and "overlay" in runs:
        baseline = set(runs["baseline"]["pytest"]["failures"])
        overlay = set(runs["overlay"]["pytest"]["failures"])
        lines += ["Only with overlay (by failing test ID; shared failures can have different causes):"]
        lines += [f"- {failure_owner(f)}: `{f}`" for f in sorted(overlay - baseline)] or ["- None."]
        lines += ["No longer failing with overlay:"]
        lines += [f"- {failure_owner(f)}: `{f}`" for f in sorted(baseline - overlay)] or ["- None."]
    current = runs.get("overlay", runs.get("baseline", {}))
    lines += probe_lines(current.get("probe", {}))
    if "freeze" in runs:
        frozen = runs["freeze"]
        before = set(current["pytest"]["failures"])
        after = set(frozen["pytest"]["failures"])
        lines += [f"- AVENIR_FREEZE=1 tests: {frozen['pytest']['summary']}",
                  f"- Freeze adds failures: {json.dumps(sorted(after - before))}",
                  f"- Freeze removes failures: {json.dumps(sorted(before - after))}",
                  f"- Freeze changes probe: {frozen['probe'] != current.get('probe')}"]
    lines += ["", "## Execution and cleanup", "", f"- Temporary worktree: {report['cleanup']}"]
    lines += [f"- {error}" for error in report["errors"]] or ["- No orchestration errors."]
    lines += ["- Missing branches are skipped. A conflict is aborted; later branches still run, without the conflicted branch.",
              "- Probe counts distinguish all ML occupations from the demo careers exposed by load_data().",
              "- Full command output is discarded to avoid copying credentials or machine details into reports.", ""]
    return "\n".join(lines)


def execute(cfg, check_runner=None):
    validate_temp(cfg)
    cfg.report_dir.mkdir(parents=True, exist_ok=True)
    cfg.temp.parent.mkdir(parents=True, exist_ok=True)
    lock = cfg.temp.parent / ".codex-integration.lock"
    # A second invocation must never remove the first invocation's active tree.
    try:
        handle = lock.open("x")
    except FileExistsError as exc:
        raise RuntimeError("Integration run already locked; inspect the active run before removing its lock") from exc
    now = london_now()
    report = {"time": now.strftime("%Y-%m-%d %H:%M %Z"), "base_sha": "unavailable", "branches": [],
              "overlay": cfg.overlay_ml, "overlay_sha": None, "runs": [], "errors": [], "cleanup": "not created"}
    created = False
    try:
        handle.write(str(os.getpid()))
        handle.close()
        # Coordination input is read on every invocation, without publishing its contents.
        status = cfg.report_dir / "claude-status.md"
        if status.is_file():
            status.read_text(encoding="utf-8")
        git(cfg.repo, "fetch", "--all", "--prune")
        report["base_sha"] = git(cfg.repo, "rev-parse", "origin/main^{commit}").stdout.strip()
        remove_temp(cfg)
        git(cfg.repo, "worktree", "add", "--detach", str(cfg.temp), report["base_sha"])
        created = True
        report["branches"] = merge_branches(cfg)
        with tempfile.TemporaryDirectory(prefix="avenir-integration-") as directory:
            artifacts = Path(directory)
            runner = check_runner or (lambda tree, label, dest: run_checks(cfg, label, dest))
            report["runs"].append(runner(cfg.temp, "baseline", artifacts))
            if cfg.overlay_ml:
                report["overlay_sha"] = overlay_ml(cfg)
                report["runs"].append(runner(cfg.temp, "overlay", artifacts))
            report["runs"].append(runner(cfg.temp, "freeze", artifacts))
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        # Exception messages may embed paths or command arguments; retain only safe categories.
        detail = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        report["errors"].append(detail if isinstance(exc, RuntimeError) else f"Execution error: {detail}")
    finally:
        if not handle.closed:
            handle.close()
        if created:
            try:
                remove_temp(cfg)
                report["cleanup"] = "removed"
            except (RuntimeError, OSError, subprocess.SubprocessError):
                report["cleanup"] = "FAILED; inspect the temporary worktree before the next run"
                report["errors"].append("Temporary worktree removal failed")
        filename = cfg.report_dir / f"integration-report-{now:%H%M}.md"
        suffix = 1
        while filename.exists():
            filename = cfg.report_dir / f"integration-report-{now:%H%M}-{suffix}.md"
            suffix += 1
        filename.write_text(render_report(report), encoding="utf-8")
        report["report"] = str(filename)
        status_lines = ["# Codex integration status", "", f"Last run: {report['time']}",
                        f"Last report: {filename.name}", f"Base: {report['base_sha']}",
                        f"Overlay: {report['overlay'] or 'none'}", "", "Branches:"]
        status_lines += [f"- {b['branch']}: {b['status']} ({b['sha'] or 'unavailable'})" for b in report["branches"]]
        status_lines += ["", "Checks:"]
        for run in report["runs"]:
            status_lines += [f"- {run['label']}: tests {run['pytest']['summary']}; lint {run['lint']['summary']}"]
            status_lines += [f"  - {failure_owner(f)}: {f}" for f in run["pytest"]["failures"]]
            status_lines += [f"  - {owner}: {message}" for owner, message in compatibility_issues(run.get("probe", {}))]
        status_lines += ["", "Blockers: " + ("; ".join(report["errors"]) or "none in harness orchestration"),
                         f"Temporary worktree: {report['cleanup']}",
                         "See the report for ML counts, flags, snapshot sizes and freeze differences.", ""]
        (cfg.report_dir / "codex-status.md").write_text("\n".join(status_lines), encoding="utf-8")
        lock.unlink()
    return report


def print_summary(report):
    branches = report["branches"]
    counts = {s: sum(b["status"] == s for b in branches) for s in ("merged", "conflict", "missing", "error")}
    tests = "; ".join(f"{r['label']}: {r['pytest']['summary']}" for r in report["runs"])
    lint = "; ".join(f"{r['label']}: {r['lint']['summary']}" for r in report["runs"] if r["label"] != "freeze")
    issues = {}
    for r in report["runs"]:
        for check in ("pytest", "lint"):
            for failure in r[check]["failures"]:
                issues.setdefault(failure_owner(failure), set()).add(failure)
        for owner, message in compatibility_issues(r.get("probe", {})):
            issues.setdefault(owner, set()).add(message)
    for branch in branches:
        for path in branch["files"]:
            issues.setdefault(failure_owner(path), set()).add(f"merge conflict: {path}")
    top = sorted(issues, key=lambda k: (-len(issues[k]), k))[:3]
    print(f"Time: {report['time']}\nBranches: {counts}\nTests: {tests or 'not run'}\nLint: {lint or 'not run'}\n"
          f"Top issues: {'; '.join(f'{owner}: {len(issues[owner])}' for owner in top) or 'none recorded'}"
          + (f"; orchestration errors: {len(report['errors'])}" if report["errors"] else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branches", help="Comma-separated remote refs; replaces defaults and automatic arsenii discovery")
    parser.add_argument("--overlay-ml", metavar="KATYATA_REF")
    parser.add_argument("--report-dir", type=Path, default=Config.report_dir)
    args = parser.parse_args()
    cfg = Config(branches=[b.strip() for b in args.branches.split(",") if b.strip()] if args.branches is not None else None,
                 overlay_ml=args.overlay_ml, report_dir=args.report_dir)
    try:
        report = execute(cfg)
    except (RuntimeError, OSError) as exc:
        print(f"Harness could not start: {exc}", file=sys.stderr)
        return 2
    print_summary(report)
    return int(bool(report["errors"] or any(b["status"] in ("conflict", "error") for b in report["branches"])
                    or any(r[c]["code"] for r in report["runs"] for c in ("pytest", "lint"))
                    or any(compatibility_issues(r.get("probe", {})) for r in report["runs"])))


if __name__ == "__main__":
    raise SystemExit(main())
