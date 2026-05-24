# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Coverage analysis — make sync gaps observable.

A core invariant of the sync topology is that coverage is *observable*: an asset
that is declared but carries no sync mode is a detectable gap, not a silent
omission. This module reports those gaps and validates a spec against a binding.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import SyncBinding, SyncSpec


@dataclass(frozen=True)
class CoverageReport:
    """Result of analysing a spec (optionally against a binding)."""

    total: int
    covered: tuple[str, ...]
    gaps: tuple[str, ...]
    unbound_folders: tuple[str, ...]
    unused_folders: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """True when every asset has a mode and (if checked) every folder binds."""
        return not self.gaps and not self.unbound_folders


def coverage_report(spec: SyncSpec, binding: SyncBinding | None = None) -> CoverageReport:
    """Analyse ``spec`` for mode gaps and, if given, binding consistency.

    - ``gaps``: asset ids declared without a sync mode.
    - ``unbound_folders``: folder names the spec references but the binding lacks.
    - ``unused_folders``: folder names the binding defines but no asset uses.
    """
    covered = tuple(a.id for a in spec.assets if a.mode is not None)
    gaps = tuple(a.id for a in spec.assets if a.mode is None)

    unbound: tuple[str, ...] = ()
    unused: tuple[str, ...] = ()
    if binding is not None:
        bound = set(binding.folders)
        used = set(spec.folders)
        unbound = tuple(sorted(used - bound))
        unused = tuple(sorted(bound - used))

    return CoverageReport(
        total=len(spec.assets),
        covered=covered,
        gaps=gaps,
        unbound_folders=unbound,
        unused_folders=unused,
    )
