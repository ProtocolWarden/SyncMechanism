# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
#!/usr/bin/env python3
"""Syncthing install/upgrade tool — version-pinned, config-archiving."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TransferSpeedColumn
from rich.table import Table

# ── paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
VERSION_FILE = SCRIPT_DIR / "version"

console = Console()
app = typer.Typer(help=__doc__, no_args_is_help=False, add_completion=False)


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _pinned() -> str:
    return VERSION_FILE.read_text().strip()


def _config_dir() -> Path:
    if _is_windows():
        return Path(os.environ["APPDATA"]) / "Syncthing"
    return Path.home() / ".local" / "share" / "syncthing"


def _archive_dir() -> Path:
    override = os.environ.get("SYNCTHING_ARCHIVE_DIR")
    if override:
        return Path(override)
    if _is_windows():
        return Path(os.environ["LOCALAPPDATA"]) / "syncthing-archives"
    return Path.home() / ".local" / "share" / "syncthing-archives"


def _install_dir() -> Path:
    if _is_windows():
        return Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Syncthing"
    return Path("/usr/local/bin")


# ── detection ─────────────────────────────────────────────────────────────────


def _installed_version() -> str:
    bin_name = "syncthing.exe" if _is_windows() else "syncthing"
    candidates: list[Path] = [_install_dir() / bin_name]
    found = shutil.which("syncthing")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            try:
                out = subprocess.check_output(
                    [str(candidate), "--version"], text=True, stderr=subprocess.DEVNULL
                )
                m = re.search(r"v(\d+\.\d+\.\d+)", out)
                if m:
                    return m.group(1)
            except (subprocess.SubprocessError, OSError):
                pass
    return ""


def _machine() -> str:
    return platform.node().split(".")[0].lower()


# ── archive index ──────────────────────────────────────────────────────────────


def _read_index() -> list[dict]:
    idx = _archive_dir() / "index.json"
    return json.loads(idx.read_text()) if idx.exists() else []


def _write_index(entries: list[dict]) -> None:
    idx = _archive_dir() / "index.json"
    idx.write_text(json.dumps(entries, indent=2) + "\n")


def _archive_config(old_version: str) -> Path:
    adir = _archive_dir()
    adir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{_machine()}_{old_version}_{ts}.zip"
    archive_path = adir / archive_name

    src = _config_dir()
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in src.rglob("*"):
            if f.is_file() and f.suffix not in (".db", ".tmp") and not f.name.startswith("index-v"):
                zf.write(f, f.relative_to(src.parent))

    entries = _read_index()
    entries.append(
        {"machine": _machine(), "version": old_version, "timestamp": ts, "archive": archive_name}
    )
    _write_index(entries)
    return archive_path


# ── download / install ─────────────────────────────────────────────────────────


def _download(version: str) -> Path:
    if _is_windows():
        filename = f"syncthing-windows-amd64-v{version}.zip"
    else:
        arch = {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "arm"}.get(
            platform.machine(), "amd64"
        )
        filename = f"syncthing-linux-{arch}-v{version}.tar.gz"

    url = f"https://github.com/syncthing/syncthing/releases/download/v{version}/{filename}"
    tmp = Path(tempfile.mkdtemp())
    dest = tmp / filename

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Downloading {filename}", total=None)

        def _hook(block: int, block_size: int, total: int) -> None:
            if total > 0:
                progress.update(task, total=total, completed=block * block_size)

        urllib.request.urlretrieve(url, dest, _hook)

    return dest


def _extract(archive: Path) -> Path:
    tmp = archive.parent
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive) as tf:
            tf.extractall(tmp)
        stem = archive.name.replace(".tar.gz", "")
        return tmp / stem / "syncthing"
    else:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmp)
        stem = archive.name.replace(".zip", "")
        return tmp / stem / "syncthing.exe"


def _install_binary(binary: Path) -> None:
    idir = _install_dir()
    idir.mkdir(parents=True, exist_ok=True)
    dest = idir / binary.name

    if _is_windows():
        shutil.copy2(binary, dest)
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            path_val, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            path_val = ""
        if str(idir) not in path_val:
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, f"{path_val};{idir}")
            console.print(f"[dim]Added {idir} to user PATH (restart shell to take effect)[/dim]")
        winreg.CloseKey(key)
    else:
        subprocess.run(["sudo", "install", "-m", "755", str(binary), str(dest)], check=True)


# ── commands ───────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _do_install()


@app.command("check")
def check() -> None:
    """Print installed vs pinned version."""
    pinned = _pinned()
    current = _installed_version()
    console.print(f"Pinned:    v{pinned}")
    console.print(f"Installed: {'v' + current if current else '(none)'}")
    if current == pinned:
        console.print("[green]status: up to date[/green]")
    else:
        console.print("[yellow]status: needs update[/yellow]")


@app.command("list")
def list_archives() -> None:
    """List config archives and their index."""
    entries = _read_index()
    if not entries:
        console.print(f"[dim]No archives in {_archive_dir()}[/dim]")
        return
    table = Table(title=str(_archive_dir()), show_lines=False)
    table.add_column("Machine", style="cyan", no_wrap=True)
    table.add_column("Version", style="yellow")
    table.add_column("Timestamp")
    table.add_column("Archive", style="dim")
    for e in entries:
        table.add_row(e["machine"], e["version"], e["timestamp"], e["archive"])
    console.print(table)


def _do_install() -> None:
    pinned = _pinned()
    current = _installed_version()

    console.print(f"Pinned:    v{pinned}")
    console.print(f"Installed: {'v' + current if current else '(none)'}")

    if current == pinned:
        console.print("[green]Already at pinned version — nothing to do.[/green]")
        raise typer.Exit()

    if current and _config_dir().exists():
        console.print(f"[blue]Archiving existing config (v{current})…[/blue]")
        path = _archive_config(current)
        console.print(f"[dim]→ {path}[/dim]")

    archive = _download(pinned)
    try:
        binary = _extract(archive)
        console.print("Installing…")
        _install_binary(binary)
    finally:
        shutil.rmtree(archive.parent, ignore_errors=True)

    console.print(f"[green]Installed: v{_installed_version()}[/green]")
    console.print(f"[dim]Archives: {_archive_dir()} — run 'install.py list' to browse[/dim]")


if __name__ == "__main__":
    app()
