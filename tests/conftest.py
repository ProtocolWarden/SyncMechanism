# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Shared fixtures for SyncMechanism tests."""

import json
import sys
from pathlib import Path

import pytest

_VENV = Path(sys.prefix)
if not (_VENV / "pyvenv.cfg").exists():
    raise RuntimeError(f"Tests must run inside a virtualenv. Active prefix: {sys.prefix}")

REPO_ROOT = Path(__file__).parent.parent
SYNCTHING_DIR = REPO_ROOT / "syncthing"

# Ensure install.py is importable
sys.path.insert(0, str(SYNCTHING_DIR))


@pytest.fixture()
def archive_dir(tmp_path: Path) -> Path:
    """Isolated archive directory with a pre-populated index."""
    adir = tmp_path / "syncthing-archives"
    adir.mkdir()
    return adir


@pytest.fixture()
def populated_archive_dir(archive_dir: Path) -> Path:
    """Archive dir with two index entries and matching zip stubs."""
    entries = [
        {
            "machine": "dev-box",
            "version": "1.25.0",
            "timestamp": "20260101T000000Z",
            "archive": "dev-box_1.25.0_20260101T000000Z.zip",
        },
        {
            "machine": "laptop",
            "version": "1.26.1",
            "timestamp": "20260201T000000Z",
            "archive": "laptop_1.26.1_20260201T000000Z.zip",
        },
    ]
    (archive_dir / "index.json").write_text(json.dumps(entries, indent=2))
    for e in entries:
        (archive_dir / e["archive"]).write_bytes(b"stub")
    return archive_dir


@pytest.fixture()
def fake_config_dir(tmp_path: Path) -> Path:
    """Minimal fake Syncthing config dir with a config.xml and a .db to skip."""
    cdir = tmp_path / "syncthing-config"
    cdir.mkdir()
    (cdir / "config.xml").write_text("<configuration></configuration>")
    (cdir / "cert.pem").write_text("cert")
    (cdir / "index-v0.14.0.db").write_bytes(b"large-db")  # should be excluded
    return cdir
