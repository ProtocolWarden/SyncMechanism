# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Login-startup management for the Syncthing tray app.

  startup enable   — register tray app to launch at login
  startup disable  — remove the login entry
  startup status   — print whether startup is currently enabled

Backends:
  Linux   — XDG autostart: ~/.config/autostart/syncthing-tray.desktop
  Windows — registry: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_LOG = logging.getLogger(__name__)

_DESKTOP_PATH = Path.home() / ".config" / "autostart" / "syncthing-tray.desktop"
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_VALUE = "SyncingTray"

_DESKTOP_TEMPLATE_XFCE = (
    "[Desktop Entry]\n"
    "Encoding=UTF-8\n"
    "Version=1.0\n"
    "Type=Application\n"
    "Name=Syncthing Tray\n"
    "Exec={cmd}\n"
    "Hidden=false\n"
    "NoDisplay=false\n"
    "OnlyShowIn=XFCE;\n"
)

_DESKTOP_TEMPLATE_XDG = (
    "[Desktop Entry]\n"
    "Type=Application\n"
    "Name=Syncthing Tray\n"
    "Exec={cmd}\n"
    "Hidden=false\n"
    "NoDisplay=false\n"
    "X-GNOME-Autostart-enabled=true\n"
)


def _desktop_template() -> str:
    import os
    import shutil

    de = os.environ.get("XDG_CURRENT_DESKTOP", "")
    if "XFCE" in de or shutil.which("xfce4-session"):
        return _DESKTOP_TEMPLATE_XFCE
    return _DESKTOP_TEMPLATE_XDG


def _tray_cmd() -> str:
    return f'"{sys.executable}" -m sync_mechanism tray'


def _is_windows() -> bool:
    return sys.platform == "win32"


# ---------------------------------------------------------------------------
# Linux — XDG autostart .desktop
# ---------------------------------------------------------------------------


def _enable_linux() -> None:
    _DESKTOP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DESKTOP_PATH.write_text(_desktop_template().format(cmd=_tray_cmd()), encoding="utf-8")
    _LOG.info("startup enabled: %s", _DESKTOP_PATH)


def _disable_linux() -> None:
    if _DESKTOP_PATH.exists():
        _DESKTOP_PATH.unlink()
        _LOG.info("startup disabled: removed %s", _DESKTOP_PATH)
    else:
        _LOG.info("startup already disabled")


def _status_linux() -> bool:
    return _DESKTOP_PATH.exists()


# ---------------------------------------------------------------------------
# Windows — HKCU Run registry key
# ---------------------------------------------------------------------------


def _enable_windows() -> None:
    import winreg  # type: ignore[import]

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, _REG_VALUE, 0, winreg.REG_SZ, _tray_cmd())
    _LOG.info("startup enabled: HKCU\\%s\\%s", _REG_KEY, _REG_VALUE)


def _disable_windows() -> None:
    import winreg  # type: ignore[import]

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _REG_VALUE)
        _LOG.info("startup disabled: removed HKCU\\%s\\%s", _REG_KEY, _REG_VALUE)
    except FileNotFoundError:
        _LOG.info("startup already disabled")


def _status_windows() -> bool:
    import winreg  # type: ignore[import]

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _REG_VALUE)
        return True
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_startup_enable(args: argparse.Namespace) -> int:
    if _is_windows():
        _enable_windows()
    else:
        _enable_linux()
    return 0


def cmd_startup_disable(args: argparse.Namespace) -> int:
    if _is_windows():
        _disable_windows()
    else:
        _disable_linux()
    return 0


def cmd_startup_status(args: argparse.Namespace) -> int:
    enabled = _status_windows() if _is_windows() else _status_linux()
    state = "enabled" if enabled else "disabled"
    _LOG.info("startup: %s", state)
    if _is_windows():
        _LOG.info("  location: HKCU\\%s\\%s", _REG_KEY, _REG_VALUE)
    else:
        _LOG.info("  location: %s", _DESKTOP_PATH)
    return 0
