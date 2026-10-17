"""Exercise the fallback scanner against real temporary Git indexes and files."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCANNER = Path(__file__).resolve().parents[1] / "check_secrets.py"


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def track(repository: Path, name: str, content: str | bytes) -> Path:
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-f", "--", name], check=True, capture_output=True)
    return path


def scan(repository: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), str(repository)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("prefix", "suffix_length", "rule"),
    [
        ("sk-", 48, "openai-key"),
        ("sk-proj-", 100, "openai-key"),
        ("sk-svcacct-", 100, "openai-key"),
        ("ghp_", 36, "github-token"),
        ("gho_", 36, "github-token"),
        ("ghu_", 36, "github-token"),
        ("ghs_", 36, "github-token"),
        ("ghr_", 76, "github-token"),
        ("github_pat_", 82, "github-token"),
        ("AKIA", 16, "aws-access-key-id"),
        ("ASIA", 16, "aws-access-key-id"),
    ],
)
def test_credential_prefix_fails_without_printing_credential(
    repository: Path, prefix: str, suffix_length: int, rule: str
) -> None:
    credential = prefix + "A" * suffix_length
    track(repository, "config.txt", f"TOKEN={credential}\n")

    result = scan(repository)

    assert result.returncode == 1
    assert "config.txt" in result.stdout
    assert rule in result.stdout
    assert credential not in result.stdout + result.stderr
    assert "TOKEN=" not in result.stdout + result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize("kind", ["", "RSA ", "EC ", "DSA ", "OPENSSH ", "ENCRYPTED "])
def test_private_key_headers_fail_without_printing_header(repository: Path, kind: str) -> None:
    header = "-" * 5 + "BEGIN " + kind + "PRIVATE KEY" + "-" * 5
    track(repository, "keys/deploy.pem", header + "\nfixture body\n")

    result = scan(repository)

    assert result.returncode == 1
    assert "keys/deploy.pem" in result.stdout
    assert "private-key" in result.stdout
    assert header not in result.stdout + result.stderr


def test_empty_example_and_ordinary_source_pass(repository: Path) -> None:
    track(repository, ".env.example", "OPENAI_API_KEY=\nGITHUB_TOKEN=\nAWS_ACCESS_KEY_ID=\n")
    track(repository, "src/settings.py", 'secret_name = "local-development"\napi_key = None\n')

    result = scan(repository)

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


@pytest.mark.parametrize("name", [".env", "apps/web/.env", ".env.local", "config/.env.production"])
def test_tracked_environment_files_fail_even_when_empty(repository: Path, name: str) -> None:
    track(repository, name, "")

    result = scan(repository)

    assert result.returncode == 1
    assert name in result.stdout
    assert "tracked-env" in result.stdout


def test_example_file_still_checks_for_credential_values(repository: Path) -> None:
    credential = "sk-" + "A" * 48
    track(repository, ".env.example", "OPENAI_API_KEY=" + credential)

    result = scan(repository)

    assert result.returncode == 1
    assert "openai-key" in result.stdout
    assert "tracked-env" not in result.stdout
    assert credential not in result.stdout + result.stderr


def test_binary_and_untracked_content_are_not_scanned(repository: Path) -> None:
    credential = "ghp_" + "A" * 36
    track(repository, "asset.bin", b"\x00\xff" + credential.encode())
    (repository / "private.txt").write_text(credential, encoding="utf-8")

    result = scan(repository)

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_current_working_content_is_scanned_after_tracking(repository: Path) -> None:
    path = track(repository, "settings.txt", "TOKEN=\n")
    path.write_text("TOKEN=" + "ghp_" + "A" * 36, encoding="utf-8")

    result = scan(repository)

    assert result.returncode == 1
    assert "github-token" in result.stdout


def test_symlinks_outside_repository_are_not_read(repository: Path, tmp_path: Path) -> None:
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (outside / "key.txt").write_text("sk-" + "A" * 48, encoding="utf-8")
    (repository / "external.txt").symlink_to(outside / "key.txt")
    subprocess.run(
        ["git", "-C", str(repository), "add", "--", "external.txt"], check=True, capture_output=True
    )

    result = scan(repository)

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_replaced_parent_symlink_cannot_escape_repository(repository: Path, tmp_path: Path) -> None:
    path = track(repository, "config/settings.txt", "TOKEN=\n")
    path.unlink()
    path.parent.rmdir()
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (outside / "settings.txt").write_text("sk-" + "A" * 48, encoding="utf-8")
    (repository / "config").symlink_to(outside, target_is_directory=True)

    result = scan(repository)

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_importable_scan_returns_only_path_and_rule(repository: Path) -> None:
    track(repository, "credential.txt", "ASIA" + "A" * 16)
    spec = importlib.util.spec_from_file_location("check_secrets", SCANNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    findings = module.scan_repository(repository)

    assert [(finding.path, finding.rule) for finding in findings] == [
        ("credential.txt", "aws-access-key-id")
    ]


def test_non_repository_fails_without_dumping_git_error(tmp_path: Path) -> None:
    result = scan(tmp_path)

    assert result.returncode != 0
    assert "git-index-unavailable" in result.stdout
    assert result.stderr == ""
