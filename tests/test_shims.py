"""Tests that shim scripts delegate to their Python entrypoints."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="bash shims not tested on Windows",
)


def _bash(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_install_sh_delegates_check():
    result = _bash("syncthing/install.sh", "check")
    assert result.returncode == 0
    assert "Pinned:" in result.stdout


def test_install_sh_delegates_list(tmp_path, monkeypatch):
    {"SYNCTHING_ARCHIVE_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        ["bash", "syncthing/install.sh", "list"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={**__import__("os").environ, "SYNCTHING_ARCHIVE_DIR": str(tmp_path)},
    )
    assert result.returncode == 0
    assert "No archives" in result.stdout
