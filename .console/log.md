# Log

_Chronological continuity log. Decisions, stop points, what changed and why._

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
