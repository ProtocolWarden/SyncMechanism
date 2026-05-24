"""Tests for syncthing/install.py."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import install

REPO_ROOT = Path(__file__).parent.parent
INSTALL_PY = REPO_ROOT / "syncthing" / "install.py"


# ── subprocess (CLI surface) ───────────────────────────────────────────────────

def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INSTALL_PY), *args],
        capture_output=True,
        text=True,
    )


def test_check_prints_pinned_and_installed():
    result = _run("check")
    assert result.returncode == 0
    assert "Pinned:" in result.stdout
    assert "Installed:" in result.stdout


def test_check_reports_status():
    result = _run("check")
    assert "status:" in result.stdout


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNCTHING_ARCHIVE_DIR", str(tmp_path / "archives"))
    result = _run("list")
    assert result.returncode == 0
    assert "No archives" in result.stdout


def test_list_shows_entries(populated_archive_dir, monkeypatch):
    monkeypatch.setenv("SYNCTHING_ARCHIVE_DIR", str(populated_archive_dir))
    result = _run("list")
    assert result.returncode == 0
    assert "dev-box" in result.stdout
    assert "1.25.0" in result.stdout
    assert "laptop" in result.stdout


# ── unit: _installed_version ───────────────────────────────────────────────────

def test_installed_version_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with patch.object(install, "_install_dir", return_value=Path("/nonexistent")):
        assert install._installed_version() == ""


def test_installed_version_found(monkeypatch, tmp_path):
    fake_bin = tmp_path / "syncthing"
    fake_bin.write_text("#!/bin/sh\necho 'syncthing v1.25.0 (go1.21)'")
    fake_bin.chmod(0o755)
    with patch.object(install, "_install_dir", return_value=tmp_path):
        version = install._installed_version()
    assert version == "1.25.0"


# ── unit: _archive_config ──────────────────────────────────────────────────────

def test_archive_config_creates_zip(fake_config_dir, archive_dir, monkeypatch):
    monkeypatch.setattr(install, "_config_dir", lambda: fake_config_dir)
    monkeypatch.setattr(install, "_archive_dir", lambda: archive_dir)
    monkeypatch.setattr(install, "_machine", lambda: "test-machine")

    path = install._archive_config("1.25.0")

    assert path.exists()
    assert path.suffix == ".zip"
    assert "test-machine" in path.name
    assert "1.25.0" in path.name


def test_archive_config_excludes_db_files(fake_config_dir, archive_dir, monkeypatch):
    monkeypatch.setattr(install, "_config_dir", lambda: fake_config_dir)
    monkeypatch.setattr(install, "_archive_dir", lambda: archive_dir)
    monkeypatch.setattr(install, "_machine", lambda: "test-machine")

    path = install._archive_config("1.25.0")

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    assert any("config.xml" in n for n in names)
    assert not any("index-v0.14.0.db" in n for n in names)


def test_archive_config_updates_index(fake_config_dir, archive_dir, monkeypatch):
    monkeypatch.setattr(install, "_config_dir", lambda: fake_config_dir)
    monkeypatch.setattr(install, "_archive_dir", lambda: archive_dir)
    monkeypatch.setattr(install, "_machine", lambda: "test-machine")

    install._archive_config("1.25.0")

    entries = json.loads((archive_dir / "index.json").read_text())
    assert len(entries) == 1
    assert entries[0]["version"] == "1.25.0"
    assert entries[0]["machine"] == "test-machine"


def test_archive_config_appends_to_existing_index(
    fake_config_dir, populated_archive_dir, monkeypatch
):
    monkeypatch.setattr(install, "_config_dir", lambda: fake_config_dir)
    monkeypatch.setattr(install, "_archive_dir", lambda: populated_archive_dir)
    monkeypatch.setattr(install, "_machine", lambda: "test-machine")

    install._archive_config("1.27.0")

    entries = json.loads((populated_archive_dir / "index.json").read_text())
    assert len(entries) == 3
    assert entries[-1]["version"] == "1.27.0"


# ── unit: _read_index / _write_index ──────────────────────────────────────────

def test_read_index_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(install, "_archive_dir", lambda: tmp_path / "empty")
    assert install._read_index() == []


def test_read_write_index_roundtrip(archive_dir, monkeypatch):
    monkeypatch.setattr(install, "_archive_dir", lambda: archive_dir)
    entries = [{"machine": "x", "version": "1.0.0", "timestamp": "t", "archive": "a.zip"}]
    install._write_index(entries)
    assert install._read_index() == entries


# ── unit: _pinned ──────────────────────────────────────────────────────────────

def test_pinned_reads_version_file():
    version = install._pinned()
    assert version  # non-empty
    parts = version.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)
