# Guidelines

_Stable repo policy. Low-churn._

## Public-safe invariant

- This repo is bound for public release. It must contain ZERO machine-specific
  data and ZERO names the boundary disclosure artifact marks as private.
- Never hardcode host-specific paths, device IDs, or references to the private
  fleet/orchestration layer. Optional integration points are env-driven
  (e.g. `SYNCTHING_TRAY_PORTFORWARD_SCRIPT`).
- The pre-push custodian guard fails closed on any forbidden name.

## Branch Policy

- Do not commit directly to `main`. Use a feature branch.
- The pre-commit hook requires a `.console/log.md` entry for source changes.

## During Work

- Run `python -m pytest -q` before and after changes.
- Run the custodian audit for boundary/lint checks before pushing.

## Scope Discipline

This repo is the generic Syncthing mechanism only. Do NOT add device
registries, fleet wiring, secrets handling, or data backup/restore — those
live in the private fleet layer that consumes this mechanism.
