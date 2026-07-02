# Log

_Chronological continuity log. Decisions, stop points, what changed and why._

## 2026-07-02 — feat(tray): declare Linux GTK bindings as a `tray-linux` extra

**Why**: On StatusNotifier desktops (Cinnamon/KDE/GNOME) pystray needs GTK
bindings (`gi`) to select its AppIndicator backend. Without them it silently
falls back to the bare XEmbed backend, which renders an icon whose right-click
menu does not work — the tray looks dead. This was hit in the field (Cinnamon
X11, venv on pyenv 3.12 sealed from the ABI-mismatched system `python3-gi`).

**What**: Added `[project.optional-dependencies].tray-linux` = PyGObject
(`>=3.50,<3.52`) + pycairo, both gated `sys_platform == 'linux'`. Upper bound is
deliberate: PyGObject 3.52+ requires `girepository-2.0`, absent on the
girepository-1.0 line (Ubuntu 22.04). Building needs system dev libs
(`libgirepository1.0-dev`, `libcairo2-dev`), noted in a pyproject comment.
Runtime deps unchanged; Windows/macOS unaffected (win32/darwin backends).

## 2026-06-26T09:52Z — feat(install): disable Syncthing's built-in self-upgrader

**Why**: SyncMechanism is the version-pinned upgrade authority, so Syncthing's own auto-upgrader is redundant — and noisy. When the binary lives in a root-owned dir (e.g. `/usr/local/bin`) but the daemon runs as a normal user, every auto-upgrade attempt fails `permission denied: open .../syncthing<rand>` and retries every few minutes forever (observed in the field).

**What**: `install` now forces `autoUpgradeIntervalH=0` on every run (idempotent; also on the already-up-to-date path). If a daemon is reachable it sets it via `syncthing cli config options auto-upgrade-intervalh set 0` (applies live + persists); otherwise it ensures a config exists (`syncthing generate`) and edits `config.xml` offline. Best-effort — never fails the install. Added `_xml_auto_upgrade_off` + offline/live tests (18 pass), README note.

## 2026-05-23 — Initial extraction of the generic Syncthing mechanism

- Created repo from the private fleet layer's generic Syncthing surface:
  `syncthing/{install,tray}.{py,sh,ps1}`, `requirements.txt`, `version`, plus
  the `install_cli`/`startup_cli` thin shims, restructured under a
  `sync_mechanism/` package with a two-command CLI (`install`, `startup`) plus
  the `tray` launcher that the startup mechanism depends on.
- Decoupled the tray's port-forward hook: removed the hardcoded private VPN
  script path; now read from the optional `SYNCTHING_TRAY_PORTFORWARD_SCRIPT`
  env var, disabled gracefully when unset.
- Relicensed moved source headers Proprietary → AGPL-3.0-or-later; added the
  AGPL-3.0 LICENSE.
- Scaffolding: pyproject (`sync-mechanism`), custodian config (repo_key
  SyncMechanism, T1/T6/T7 exclusions for the thin CLI shims), hooks, gitignore,
  README/CHANGELOG/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT.
- Verified: tests green, custodian clean, forbidden-name grep empty.

## 2026-05-24 — Build the sync-spec contract

- Added sync_mechanism/spec/ (modes, models, loader, coverage) — the manifest-declared vocabulary: SyncMode (copy/in-repo/external), SyncSpec public shape + SyncBinding private binding, YAML loader/validator, coverage gap detection + spec/binding resolution.
- New `spec` CLI (validate/coverage/resolve) + examples/. Narrowed custodian T1/T6/T7 exclusions to shim modules only (spec/ is real-tested). PyYAML dep. 26 new tests (71 total).

## 2026-06-04 — Console reconciliation: enforce R1/R2

- ENFORCE-ONLY pass per the console-reconciliation spec. .console/ is already
  clean (forbidden-name grep empty on tracked .console/docs) and under budget
  (log.md = 25 lines, well under the R1 400-line budget); no prune needed.
- Set `audit.reconcile_enforce: true` in `.custodian/config.yaml` so the
  Custodian R1 (over-budget) and R2 (scrub-target leak) detectors enforce here.
- Verified `cl reconcile check` GREEN; custodian audit gains no R1/R2 findings.
