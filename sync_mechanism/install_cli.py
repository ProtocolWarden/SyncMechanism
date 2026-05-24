# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Syncthing install / upgrade / archive commands (delegates to syncthing/install.py)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_INSTALL_PY = Path(__file__).resolve().parents[1] / "syncthing" / "install.py"


def _python() -> str:
    return sys.executable


def cmd_install(args: argparse.Namespace) -> int:
    return subprocess.run([_python(), str(_INSTALL_PY)], timeout=300).returncode


def cmd_install_check(args: argparse.Namespace) -> int:
    return subprocess.run([_python(), str(_INSTALL_PY), "check"], timeout=30).returncode


def cmd_install_list(args: argparse.Namespace) -> int:
    return subprocess.run([_python(), str(_INSTALL_PY), "list"], timeout=30).returncode
