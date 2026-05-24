# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Generic, public-safe Syncthing mechanism extracted from a private fleet
  layer: version-pinned install/upgrade with config archiving (`install`), a
  desktop tray launcher (`tray`), and login-startup registration (`startup`).
- Optional, env-driven port-forward hook for the tray
  (`SYNCTHING_TRAY_PORTFORWARD_SCRIPT`); disabled when unset.
- **Sync-spec contract** (`sync_mechanism/spec/`): the manifest-declared
  vocabulary for fleet data sync — `SyncMode` (copy/in-repo/external),
  `SyncSpec` (public shape) and `SyncBinding` (private binding), YAML
  loader/validator, and coverage analysis (declared-but-modeless assets surface
  as gaps; spec/binding folder consistency is checked). New `spec`
  CLI (`validate` / `coverage` / `resolve`) and `examples/` declarations.
- AGPL-3.0-or-later license.
