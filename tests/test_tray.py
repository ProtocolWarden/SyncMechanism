# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for syncthing/tray.py — headless-safe parts only."""

import os

# pystray picks an X11 backend at import and dies on a headless runner
# (Xlib DisplayNameError) — force the dummy backend before `tray` pulls it in.
os.environ.setdefault("PYSTRAY_BACKEND", "dummy")

from unittest.mock import patch

import tray

# ── icon ──────────────────────────────────────────────────────────────────────


def test_make_icon_returns_image():
    from PIL import Image

    img = tray._make_icon()
    assert isinstance(img, Image.Image)


def test_make_icon_dimensions():
    img = tray._make_icon()
    assert img.size == (64, 64)


def test_make_icon_has_alpha():
    img = tray._make_icon()
    assert img.mode == "RGBA"


# ── terminal detection ─────────────────────────────────────────────────────────


def test_find_terminal_returns_none_when_nothing_available():
    with patch("shutil.which", return_value=None):
        assert tray._find_terminal() is None


def test_find_terminal_detects_konsole():
    def fake_which(cmd):
        return "/usr/bin/konsole" if cmd == "konsole" else None

    with patch("shutil.which", side_effect=fake_which):
        result = tray._find_terminal()
    assert result is not None
    assert "konsole" in result[0]


def test_find_terminal_detects_mate_terminal():
    def fake_which(cmd):
        return "/usr/bin/mate-terminal" if cmd == "mate-terminal" else None

    with patch("shutil.which", side_effect=fake_which):
        result = tray._find_terminal()
    assert result is not None
    assert "mate-terminal" in result[0]


def test_find_terminal_detects_tilix():
    def fake_which(cmd):
        return "/usr/bin/tilix" if cmd == "tilix" else None

    with patch("shutil.which", side_effect=fake_which):
        result = tray._find_terminal()
    assert result is not None
    assert "tilix" in result[0]


def test_find_terminal_prefers_konsole_over_xterm():
    def fake_which(cmd):
        return f"/usr/bin/{cmd}" if cmd in ("konsole", "xterm") else None

    with patch("shutil.which", side_effect=fake_which):
        result = tray._find_terminal()
    assert result is not None
    assert result[0] == "konsole"


# ── paths ─────────────────────────────────────────────────────────────────────


def test_repo_root_exists():
    assert tray.REPO_ROOT.is_dir(), f"REPO_ROOT not found at {tray.REPO_ROOT}"


def test_cli_command_uses_sync_mechanism():
    cmd = tray._cli("install", "check")
    assert "-m" in cmd
    assert "sync_mechanism" in cmd
