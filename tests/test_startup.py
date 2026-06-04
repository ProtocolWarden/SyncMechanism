# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for sync_mechanism/startup_cli.py."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import sync_mechanism.startup_cli as startup

# ── helpers ───────────────────────────────────────────────────────────────────


class _Args:
    pass


def _winreg_mock(value_exists: bool = True) -> MagicMock:
    """Minimal winreg stand-in."""
    m = MagicMock()
    m.HKEY_CURRENT_USER = 0x80000001
    m.KEY_SET_VALUE = 0x0002
    m.KEY_READ = 0x20019
    m.REG_SZ = 1
    if not value_exists:
        m.QueryValueEx.side_effect = FileNotFoundError
        m.DeleteValue.side_effect = FileNotFoundError
    return m


# ── tray command ──────────────────────────────────────────────────────────────


def test_tray_cmd_contains_executable():
    assert sys.executable in startup._tray_cmd()


def test_tray_cmd_contains_module_and_subcommand():
    cmd = startup._tray_cmd()
    assert "sync_mechanism" in cmd
    assert "tray" in cmd


# ── Linux: _enable_linux ──────────────────────────────────────────────────────


def test_enable_linux_creates_desktop_file(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        startup._enable_linux()
    assert desktop.exists()


def test_enable_linux_desktop_content(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        startup._enable_linux()
    text = desktop.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in text
    assert "Type=Application" in text
    assert "X-GNOME-Autostart-enabled=true" in text
    assert "sync_mechanism" in text
    assert "tray" in text


def test_enable_linux_creates_parent_dirs(tmp_path):
    desktop = tmp_path / "deeply" / "nested" / "syncthing-tray.desktop"
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        startup._enable_linux()
    assert desktop.exists()


# ── Linux: _disable_linux ─────────────────────────────────────────────────────


def test_disable_linux_removes_file(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    desktop.parent.mkdir(parents=True)
    desktop.write_text("x", encoding="utf-8")
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        startup._disable_linux()
    assert not desktop.exists()


def test_disable_linux_no_error_when_absent(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        startup._disable_linux()
    assert not desktop.exists()


# ── Linux: _status_linux ──────────────────────────────────────────────────────


def test_status_linux_true_when_file_exists(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    desktop.parent.mkdir(parents=True)
    desktop.write_text("x", encoding="utf-8")
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        assert startup._status_linux() is True


def test_status_linux_false_when_absent(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with patch.object(startup, "_DESKTOP_PATH", desktop):
        assert startup._status_linux() is False


# ── Windows: _enable_windows ──────────────────────────────────────────────────


def test_enable_windows_calls_set_value_ex():
    wr = _winreg_mock()
    with patch.dict(sys.modules, {"winreg": wr}):
        startup._enable_windows()
    wr.SetValueEx.assert_called_once()
    args = wr.SetValueEx.call_args[0]
    assert startup._REG_VALUE in args
    assert "sync_mechanism" in args[-1]


# ── Windows: _disable_windows ─────────────────────────────────────────────────


def test_disable_windows_calls_delete_value():
    wr = _winreg_mock()
    with patch.dict(sys.modules, {"winreg": wr}):
        startup._disable_windows()
    wr.DeleteValue.assert_called_once()


def test_disable_windows_no_error_when_absent():
    wr = _winreg_mock(value_exists=False)
    with patch.dict(sys.modules, {"winreg": wr}):
        startup._disable_windows()
    wr.DeleteValue.assert_called_once()


# ── Windows: _status_windows ──────────────────────────────────────────────────


def test_status_windows_true_when_value_exists():
    wr = _winreg_mock(value_exists=True)
    with patch.dict(sys.modules, {"winreg": wr}):
        assert startup._status_windows() is True


def test_status_windows_false_when_value_absent():
    wr = _winreg_mock(value_exists=False)
    with patch.dict(sys.modules, {"winreg": wr}):
        assert startup._status_windows() is False


# ── cmd dispatch ──────────────────────────────────────────────────────────────


def test_cmd_enable_linux(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with (
        patch.object(startup, "_DESKTOP_PATH", desktop),
        patch.object(startup, "_is_windows", return_value=False),
    ):
        rc = startup.cmd_startup_enable(_Args())
    assert rc == 0
    assert desktop.exists()


def test_cmd_disable_linux(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    desktop.parent.mkdir(parents=True)
    desktop.write_text("x", encoding="utf-8")
    with (
        patch.object(startup, "_DESKTOP_PATH", desktop),
        patch.object(startup, "_is_windows", return_value=False),
    ):
        rc = startup.cmd_startup_disable(_Args())
    assert rc == 0
    assert not desktop.exists()


def test_cmd_status_returns_zero(tmp_path):
    desktop = tmp_path / "autostart" / "syncthing-tray.desktop"
    with (
        patch.object(startup, "_DESKTOP_PATH", desktop),
        patch.object(startup, "_is_windows", return_value=False),
    ):
        assert startup.cmd_startup_status(_Args()) == 0


def test_cmd_enable_windows():
    wr = _winreg_mock()
    with (
        patch.object(startup, "_is_windows", return_value=True),
        patch.dict(sys.modules, {"winreg": wr}),
    ):
        assert startup.cmd_startup_enable(_Args()) == 0
    wr.SetValueEx.assert_called_once()


def test_cmd_disable_windows():
    wr = _winreg_mock()
    with (
        patch.object(startup, "_is_windows", return_value=True),
        patch.dict(sys.modules, {"winreg": wr}),
    ):
        assert startup.cmd_startup_disable(_Args()) == 0
    wr.DeleteValue.assert_called_once()


def test_cmd_status_windows():
    wr = _winreg_mock(value_exists=True)
    with (
        patch.object(startup, "_is_windows", return_value=True),
        patch.dict(sys.modules, {"winreg": wr}),
    ):
        assert startup.cmd_startup_status(_Args()) == 0
