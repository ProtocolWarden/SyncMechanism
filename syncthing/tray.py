# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
#!/usr/bin/env python3
"""
Syncthing Tools — system tray app.

Sits in the tray and provides one-click access to install, check, and
list-archives without opening a terminal manually, plus a toggle for
launching the tray at login.

Usage:
    python3 syncthing/tray.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pystray
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent

# Optional, host-supplied port-forward helper. When the environment variable is
# unset or empty the feature is disabled and the tray runs without it. The
# integrating (private) layer may point this at its own VPN port-forward script.
_pf_env = os.environ.get("SYNCTHING_TRAY_PORTFORWARD_SCRIPT", "")
_PORTFORWARD_SCRIPT: Optional[Path] = Path(_pf_env) if _pf_env else None

_pf_proc: Optional[subprocess.Popen] = None  # type: ignore[type-arg]

# ── icon ──────────────────────────────────────────────────────────────────────


def _make_icon() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Filled circle
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(32, 156, 238, 255))
    # Two small arrow chevrons (▶▶) to suggest sync
    cx, cy = size // 2, size // 2
    for offset in (-7, 5):
        x = cx + offset
        draw.polygon([(x, cy - 10), (x + 9, cy), (x, cy + 10)], fill=(255, 255, 255, 220))
    return img


# ── terminal runner ────────────────────────────────────────────────────────────


def _find_terminal() -> list[str] | None:
    """Return a command prefix that opens a new terminal window and runs its args."""
    candidates = [
        # KDE (Manjaro KDE, Kubuntu)
        (["konsole", "-e"], "konsole"),
        # XFCE (Manjaro XFCE, Mint XFCE)
        (["xfce4-terminal", "-x"], "xfce4-terminal"),
        # MATE (Mint MATE)
        (["mate-terminal", "-x"], "mate-terminal"),
        # Tilix (Mint Cinnamon popular choice)
        (["tilix", "-e"], "tilix"),
        # GNOME / Mint Cinnamon fallback
        (["gnome-terminal", "--"], "gnome-terminal"),
        # Generic fallbacks
        (["kitty"], "kitty"),
        (["alacritty", "-e"], "alacritty"),
        (["xterm", "-e"], "xterm"),
    ]
    for prefix, binary in candidates:
        if shutil.which(binary):
            return prefix
    return None


def _run_in_terminal(cmd: list[str]) -> None:
    if platform.system() == "Windows":
        subprocess.Popen(
            ["cmd", "/c", *cmd, "&", "pause"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,  # type: ignore[attr-defined]
        )
        return

    prefix = _find_terminal()
    if prefix is None:
        # No graphical terminal found — fall back to running detached (output lost)
        subprocess.Popen(cmd, start_new_session=True)
        return

    # konsole / xfce4-terminal use -e <cmd> [args...]
    # gnome-terminal uses -- <cmd> [args...]
    subprocess.Popen(prefix + cmd, start_new_session=True)


def _python() -> str:
    return sys.executable


def _cli(*args: str) -> list[str]:
    return [_python(), "-m", "sync_mechanism", *args]


# ── menu actions ──────────────────────────────────────────────────────────────


def _action_check(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    _run_in_terminal(_cli("install", "check"))


def _action_install(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    _run_in_terminal(_cli("install"))


def _action_list(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    _run_in_terminal(_cli("install", "list"))


def _startup_is_enabled(item: pystray.MenuItem) -> bool:
    from sync_mechanism.startup_cli import _is_windows, _status_linux, _status_windows

    return _status_windows() if _is_windows() else _status_linux()


def _action_toggle_startup(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    from sync_mechanism.startup_cli import (
        _disable_linux,
        _disable_windows,
        _enable_linux,
        _enable_windows,
        _is_windows,
    )

    if _startup_is_enabled(item):
        _disable_windows() if _is_windows() else _disable_linux()
    else:
        _enable_windows() if _is_windows() else _enable_linux()


def _action_quit(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    global _pf_proc
    if _pf_proc is not None and _pf_proc.poll() is None:
        _pf_proc.terminate()
        _pf_proc = None
    icon.stop()


# ── entry ─────────────────────────────────────────────────────────────────────


def _start_portforward() -> None:
    global _pf_proc
    if platform.system() == "Windows":
        return
    if _PORTFORWARD_SCRIPT is None or not _PORTFORWARD_SCRIPT.exists():
        return
    _pf_proc = subprocess.Popen(
        ["bash", str(_PORTFORWARD_SCRIPT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main() -> None:
    _start_portforward()
    icon = pystray.Icon(
        name="syncthing-tools",
        icon=_make_icon(),
        title="Syncthing Tools",
        menu=pystray.Menu(
            pystray.MenuItem("Check version", _action_check),
            pystray.MenuItem("Install / Upgrade", _action_install),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Launch at login", _action_toggle_startup, checked=_startup_is_enabled
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("List archives", _action_list),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _action_quit),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
