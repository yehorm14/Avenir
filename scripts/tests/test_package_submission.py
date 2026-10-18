"""Exercise the delivery archive against real Git repositories and built assets."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "package_submission.py"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def release(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q")
    for name, body in {
        "README.md": "Demo setup\n",
        "pyproject.toml": '[project]\nname = "demo"\n',
        "apps/web/src/main.tsx": "export const demo = true;\n",
        ".env.example": "OPTIONAL_KEY=\n",
        "data/raw/.gitkeep": "",
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    dist = root / "apps/web/dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text('<html><script src="/assets/app.js"></script></html>')
    (dist / "assets/app.js").write_text("console.log('ready');")
    return root


def package(root: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--output", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_archive_contains_tracked_source_and_working_bundle_without_local_extras(release: Path, tmp_path: Path):
    for name in (".env", "apps/web/node_modules/local.txt", "data/raw/private.csv"):
        path = release / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("local only")
    output = tmp_path / "submission.zip"

    result = package(release, output)

    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert {
            "README.md",
            "pyproject.toml",
            ".env.example",
            "apps/web/src/main.tsx",
            "apps/web/dist/index.html",
            "apps/web/dist/assets/app.js",
            "SUBMISSION.json",
        } <= names
        assert not any(
            "node_modules" in name or "data/raw/" in name or name == ".env" or name.startswith(".git/") for name in names
        )
        manifest = json.loads(archive.read("SUBMISSION.json"))
        assert manifest["revision"] == git(release, "rev-parse", "HEAD")
        for name, digest in manifest["sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest


def test_missing_asset_rejects_incomplete_bundle(release: Path, tmp_path: Path):
    (release / "apps/web/dist/assets/app.js").unlink()
    output = tmp_path / "submission.zip"
    result = package(release, output)
    assert result.returncode != 0
    assert "build" in result.stderr.lower()
    assert not output.exists()


def test_dirty_tracked_source_requires_checkpoint(release: Path, tmp_path: Path):
    (release / "README.md").write_text("uncommitted edit")
    output = tmp_path / "submission.zip"
    result = package(release, output)
    assert result.returncode != 0
    assert "commit" in result.stderr.lower()
    assert not output.exists()


@pytest.mark.usefixtures("requires_symlinks")
def test_bundle_symlink_cannot_export_an_external_file(release: Path, tmp_path: Path):
    external = tmp_path / "outside.txt"
    external.write_text("not part of project")
    (release / "apps/web/dist/assets/outside.txt").symlink_to(external)
    output = tmp_path / "submission.zip"
    result = package(release, output)
    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()
    assert not output.exists()


def test_existing_delivery_is_never_overwritten(release: Path, tmp_path: Path):
    output = tmp_path / "submission.zip"
    output.write_bytes(b"previous delivery")
    result = package(release, output)
    assert result.returncode != 0
    assert output.read_bytes() == b"previous delivery"


def test_tracked_environment_file_blocks_delivery_without_revealing_contents(release: Path, tmp_path: Path):
    (release / ".env").write_text("LOCAL_VALUE=private-fixture")
    git(release, "add", "-f", ".env")
    git(release, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "unsafe fixture")
    output = tmp_path / "submission.zip"
    result = package(release, output)
    assert result.returncode != 0
    assert "private-fixture" not in result.stdout + result.stderr
    assert not output.exists()
