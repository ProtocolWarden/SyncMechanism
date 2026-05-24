# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""CLI commands for working with sync specs: validate, coverage, resolve."""

from __future__ import annotations

import argparse

from .spec import (
    SpecParseError,
    UnboundFolderError,
    coverage_report,
    load_binding,
    load_spec,
)


def cmd_spec_validate(args: argparse.Namespace) -> int:
    """Parse + validate a sync spec (and binding, if given). Exit 0 if valid."""
    try:
        spec = load_spec(args.spec)
        if args.binding:
            load_binding(args.binding)
    except SpecParseError as exc:
        print(f"invalid: {exc}")
        return 1
    print(f"valid: {spec.scope} — {len(spec.assets)} asset(s), schema {spec.schema_version}")
    return 0


def cmd_spec_coverage(args: argparse.Namespace) -> int:
    """Report mode gaps and (with a binding) folder consistency. Exit 1 if not clean."""
    try:
        spec = load_spec(args.spec)
        binding = load_binding(args.binding) if args.binding else None
    except SpecParseError as exc:
        print(f"invalid: {exc}")
        return 2

    report = coverage_report(spec, binding)
    print(f"scope: {spec.scope}")
    print(f"assets: {report.total}  covered: {len(report.covered)}  gaps: {len(report.gaps)}")
    for gap in report.gaps:
        print(f"  GAP   {gap}  (no sync mode declared)")
    for folder in report.unbound_folders:
        print(f"  UNBOUND folder {folder!r} referenced by spec but missing from binding")
    for folder in report.unused_folders:
        print(f"  note: binding folder {folder!r} is unused by the spec")
    print("clean" if report.is_clean else "NOT clean")
    return 0 if report.is_clean else 1


def cmd_spec_resolve(args: argparse.Namespace) -> int:
    """Join a spec against a binding and print the transport plan. Exit 1 on unbound folders."""
    try:
        spec = load_spec(args.spec)
        binding = load_binding(args.binding)
    except SpecParseError as exc:
        print(f"invalid: {exc}")
        return 2
    try:
        resolved = spec.resolve(binding)
    except UnboundFolderError as exc:
        print(f"unresolved: {exc}")
        return 1
    for r in resolved:
        mode = r.asset.mode if r.asset.mode is not None else "(no mode)"
        devices = ",".join(r.binding.devices) or "(no devices)"
        print(f"{r.asset.id}: {mode} {r.asset.source} -> {r.binding.path} [{devices}]")
    return 0
