# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Sync-spec contract: the manifest-declared vocabulary for fleet data sync.

This package defines *what a manifest declares* about syncing — the public shape
(:class:`SyncSpec`) and the private binding (:class:`SyncBinding`) — plus loading,
validation, and coverage analysis. The actual transport orchestration
(backup/restore, emitting Syncthing config) is built on top of this contract.
"""

from __future__ import annotations

from .coverage import CoverageReport, coverage_report
from .loader import (
    SpecParseError,
    load_binding,
    load_spec,
    parse_binding,
    parse_spec,
)
from .models import (
    FolderBinding,
    ResolvedAsset,
    SyncAsset,
    SyncBinding,
    SyncSpec,
    UnboundFolderError,
)
from .modes import SyncMode

__all__ = [
    "SyncMode",
    "SyncAsset",
    "SyncSpec",
    "FolderBinding",
    "SyncBinding",
    "ResolvedAsset",
    "UnboundFolderError",
    "load_spec",
    "load_binding",
    "parse_spec",
    "parse_binding",
    "SpecParseError",
    "coverage_report",
    "CoverageReport",
]
