#!/usr/bin/env python3
"""Small current-tree credential check; supplements a dedicated secret scanner.

Only Git-tracked UTF-8 text is inspected. Findings contain paths and rule names,
never matching values or source excerpts. History and untracked files are outside
this check's scope. Symlinks and binary/non-UTF-8 files are skipped.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    path: str
    rule: str


RULES = (
    (
        "openai-key",
        re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])"),
    ),
    (
        "github-token",
        re.compile(r"(?<![A-Za-z0-9_])(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}(?![A-Za-z0-9_])"),
    ),
    (
        "aws-access-key-id",
        re.compile(r"(?<![A-Za-z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Za-z0-9])"),
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:(?:RSA|EC|DSA|OPENSSH|ENCRYPTED) )?PRIVATE KEY-----"),
    ),
)


def scan_text(path: str, text: str) -> list[Finding]:
    """Return one redacted finding per matching credential rule in a text file."""
    return [Finding(path, name) for name, pattern in RULES if pattern.search(text)]


def scan_repository(repository: Path) -> list[Finding]:
    """Inspect current working copies of tracked files under a Git repository root."""
    root = repository.resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--full-name", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [Finding(".", "git-index-unavailable")]

    findings = []
    for name in sorted(set(os.fsdecode(item) for item in result.stdout.split(b"\0") if item)):
        relative = Path(name)
        if relative.name != ".env.example" and (
            relative.name == ".env" or relative.name.startswith(".env.")
        ):
            findings.append(Finding(name, "tracked-env"))
        candidate = root / relative
        try:
            if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
                continue
            if not candidate.is_file():
                continue
            data = candidate.read_bytes()
        except FileNotFoundError:
            # A tracked deletion has no current-tree content to inspect.
            continue
        except OSError:
            findings.append(Finding(name, "unreadable-tracked-file"))
            continue
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(name, text))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    """Print only escaped paths and rule names; return nonzero for findings/errors."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        findings = [Finding(".", "invalid-arguments")]
    else:
        repository = Path(args[0]) if args else Path(__file__).resolve().parents[1]
        findings = scan_repository(repository)
    for finding in findings:
        print(f"{json.dumps(finding.path, ensure_ascii=True)}: {finding.rule}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
