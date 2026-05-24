# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Sync-spec vocabulary: the closed set of sync modes a manifest may declare.

A *sync mode* answers "how does this asset travel between machines?". It is the
core public vocabulary of the sync topology (see the PlatformDeployment ADR
"Sync topology: manifest as sync authority"). The legal values live here, in the
public mechanism, so every manifest declares against one source of truth.
"""

from __future__ import annotations

from enum import Enum


class SyncMode(str, Enum):
    """How a sync asset is transported.

    - ``COPY``    — small things snapshotted into a ``sync/`` directory.
    - ``IN_REPO`` — large things synced in place (e.g. model/media files).
    - ``EXTERNAL``— things that cannot live in-repo, synced from an
      out-of-tree location (e.g. large backup archives).
    """

    COPY = "copy"
    IN_REPO = "in-repo"
    EXTERNAL = "external"

    def __str__(self) -> str:  # render as the wire value, not "SyncMode.COPY"
        return self.value

    @classmethod
    def from_value(cls, value: str) -> "SyncMode":
        """Parse a declared string into a SyncMode, with a helpful error.

        Raises ``ValueError`` naming the legal values when ``value`` is unknown.
        """
        try:
            return cls(value)
        except ValueError as exc:
            legal = ", ".join(repr(m.value) for m in cls)
            raise ValueError(
                f"unknown sync mode {value!r}; legal modes are: {legal}"
            ) from exc
