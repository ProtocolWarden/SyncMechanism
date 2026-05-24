# SyncMechanism

Generic, public-safe Syncthing install and runtime mechanism — version
pinning, config archiving, a desktop tray, and login-startup registration.
Config-driven, with zero machine-specific data.

```text
sync-mechanism install        →  install / upgrade Syncthing to the pinned version
sync-mechanism install check  →  compare installed vs pinned version
sync-mechanism install list   →  list config archives
sync-mechanism tray           →  start the system tray app
sync-mechanism startup enable →  launch the tray at login
```

## What this repo is

- A version-pinned Syncthing **install / upgrade** tool that archives the
  existing config before replacing the binary (`syncthing/install.py`,
  `syncthing/version`).
- A desktop **tray app** for one-click install/check/list and a login-startup
  toggle (`syncthing/tray.py`).
- A **login-startup** mechanism: XDG autostart on Linux, HKCU Run registry
  value on Windows (`sync_mechanism/startup_cli.py`).
- A small unified CLI (`python -m sync_mechanism`) wiring `install`, `tray`,
  and `startup`.
- Entirely config-driven and public-safe — no host-specific data is baked in.

## What this repo is not

- **Not** a device or folder registry — there is no `devices.yaml`, no
  topology, no machine list here.
- **Not** a holder of secrets or credentials.
- **Not** fleet wiring or data backup/restore. Those concerns live in the
  private fleet layer that *consumes* this mechanism.
- **Not** a Syncthing fork — it installs upstream Syncthing release binaries.

Integration points a private layer needs are exposed as environment variables
(e.g. `SYNCTHING_TRAY_PORTFORWARD_SCRIPT`), never hardcoded.

## Quick start

```bash
pip install -e .                          # installs the sync_mechanism package

python -m sync_mechanism install          # install / upgrade Syncthing to pinned version
python -m sync_mechanism install check    # compare installed vs pinned version
python -m sync_mechanism tray             # start the system tray app
python -m sync_mechanism startup enable   # launch the tray at login
```

**Tray app — Linux system tray dependencies** require a working system tray
(via `pystray` + `Pillow`, installed as dependencies) and a graphical session.

### Pinned version

The target Syncthing version is pinned in `syncthing/version`. `install`
compares it against the installed binary and upgrades only when they differ,
archiving the existing config first.

### Config archive location

Archives default to `~/.local/share/syncthing-archives` (Linux) or
`%LOCALAPPDATA%\syncthing-archives` (Windows). Override with the
`SYNCTHING_ARCHIVE_DIR` environment variable.

## Architecture

```text
python -m sync_mechanism <command>
        │
        ├─ install [check|list]  ─→ sync_mechanism/install_cli.py ─→ syncthing/install.py
        ├─ tray                  ─→ syncthing/tray.py  (pystray + Pillow)
        └─ startup [enable|disable|status] ─→ sync_mechanism/startup_cli.py
                                              ├─ Linux:   ~/.config/autostart/*.desktop
                                              └─ Windows: HKCU\...\Run
```

- `sync_mechanism/` holds thin CLI shims; the actual install/tray work lives in
  `syncthing/*.py`.
- `install.py` downloads version-pinned upstream Syncthing release archives over
  HTTPS, archives the existing config, and installs the new binary.
- `tray.py` provides the desktop menu and an optional, env-driven port-forward
  hook for the integrating layer.
- `startup_cli.py` registers/deregisters the tray at login on both Linux and
  Windows.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
