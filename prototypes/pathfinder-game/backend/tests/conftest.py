"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def requires_symlinks(tmp_path: Path) -> None:
    """Skip the test where the OS refuses symlink creation (e.g. Windows without Developer Mode)."""
    target = tmp_path / "_symlink_probe_target"
    target.write_text("probe")
    try:
        (tmp_path / "_symlink_probe_link").symlink_to(target)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"OS does not permit creating symlinks: {error}")
