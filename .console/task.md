# Task

## Objective

Maintain the generic, public-safe Syncthing install/runtime/startup mechanism.

## Context

Extracted from a private fleet-management layer. This repo owns only the
config-driven mechanism: version-pinned install/upgrade, config archiving, a
desktop tray, and login-startup registration. No device registry, no secrets,
no fleet wiring.

## Definition of Done

`pip install -e .` works, `python -m pytest -q` is green, and the custodian
audit reports zero findings with zero private/forbidden names.
