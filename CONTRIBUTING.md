# Contributing to SyncMechanism

SyncMechanism is the generic, public-safe Syncthing install and runtime
mechanism: version-pinned install/upgrade, config archiving, a desktop tray,
and login-startup registration. It is config-driven and contains no
machine-specific data.

## Before You Start

- Check open issues to avoid duplicate work.
- For significant changes, open an issue first to discuss the approach.
- All contributions must pass the test suite and linter before merging.

## Development Setup

```bash
git clone https://github.com/ProtocolWarden/SyncMechanism.git
cd SyncMechanism
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest -q
```

## Linting

```bash
ruff check sync_mechanism/ syncthing/
```

## Scope Discipline

SyncMechanism intentionally has a narrow scope. Do **not** add:

- Device/folder registries or fleet topology
- Secrets handling or credential storage
- Data backup/restore or any synced data
- Host-specific paths, device IDs, or references to a private fleet layer

Integration points that a private layer needs are exposed as environment
variables (e.g. `SYNCTHING_TRAY_PORTFORWARD_SCRIPT`), never hardcoded.

## Pull Request Checklist

- [ ] Tests added for new behavior
- [ ] Existing tests still pass (`python -m pytest -q`)
- [ ] Linter passes
- [ ] No machine-specific data or private names introduced
- [ ] Public API changes are reflected in the README

## Code Style

- Type hints on public functions
- No `from foo import *`
- Comments only when the *why* is non-obvious
