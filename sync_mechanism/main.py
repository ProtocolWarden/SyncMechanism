# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""SyncMechanism CLI — generic Syncthing install and login-startup mechanism."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

from .install_cli import cmd_install, cmd_install_check, cmd_install_list
from .startup_cli import cmd_startup_disable, cmd_startup_enable, cmd_startup_status

_TRAY_PY = Path(__file__).resolve().parents[1] / "syncthing" / "tray.py"


def _cmd_tray(args: argparse.Namespace) -> int:
    return subprocess.run([sys.executable, str(_TRAY_PY)], timeout=None).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync_mechanism",
        description="SyncMechanism — generic Syncthing install and login-startup mechanism.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # -- install ---------------------------------------------------------------
    p_install = sub.add_parser(
        "install", help="Install or upgrade Syncthing to the pinned version."
    )
    install_sub = p_install.add_subparsers(dest="install_action", metavar="<action>")

    p_install_check = install_sub.add_parser("check", help="Compare installed vs pinned version.")
    p_install_check.set_defaults(func=cmd_install_check)

    p_install_list = install_sub.add_parser(
        "list", help="List config archives with machine/version/timestamp."
    )
    p_install_list.set_defaults(func=cmd_install_list)

    def _install_default(args: argparse.Namespace) -> int:
        return cmd_install(args)

    p_install.set_defaults(func=_install_default)

    # -- tray ------------------------------------------------------------------
    p_tray = sub.add_parser("tray", help="Start the system tray app.")
    p_tray.set_defaults(func=_cmd_tray)

    # -- startup ---------------------------------------------------------------
    p_startup = sub.add_parser(
        "startup", help="Enable or disable tray app at login."
    )
    startup_sub = p_startup.add_subparsers(dest="startup_action", metavar="<action>")

    p_startup_enable = startup_sub.add_parser(
        "enable", help="Register tray app to launch at login."
    )
    p_startup_enable.set_defaults(func=cmd_startup_enable)

    p_startup_disable = startup_sub.add_parser(
        "disable", help="Remove tray app from login startup."
    )
    p_startup_disable.set_defaults(func=cmd_startup_disable)

    p_startup_status = startup_sub.add_parser(
        "status", help="Print whether startup is currently enabled."
    )
    p_startup_status.set_defaults(func=cmd_startup_status)

    def _startup_help(args: argparse.Namespace) -> int:
        p_startup.print_help()
        return 0

    p_startup.set_defaults(func=_startup_help)

    return parser


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )


def main() -> NoReturn:
    _configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
