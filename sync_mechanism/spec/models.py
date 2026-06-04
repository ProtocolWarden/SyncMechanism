# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Sync-spec data model — the contract a manifest declares.

Two layers, mirroring the public-mechanism / private-binding split:

- :class:`SyncSpec` is the **public shape**: which assets sync, their mode, their
  logical source, and the *named* Syncthing folder they belong to. It carries no
  device IDs, no absolute destination paths, and no secrets, so it is safe to
  declare in a public manifest.
- :class:`SyncBinding` is the **private binding**: it maps each folder name to a
  concrete Syncthing folder id, on-disk path, and device set. It lives in the
  private fleet layer, never in a public repo.

:func:`SyncSpec.resolve` joins the two into a :class:`ResolvedAsset` plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .modes import SyncMode


@dataclass(frozen=True)
class SyncAsset:
    """One declared unit of syncable data (public shape).

    ``mode`` is intentionally optional: a declared asset with ``mode=None`` is a
    *known but uncovered* asset — a detectable coverage gap, not a silent
    omission (see :func:`sync_mechanism.spec.coverage.coverage_report`).
    """

    id: str
    source: str
    folder: str
    data_class: str = "operational"
    mode: SyncMode | None = None

    def __post_init__(self) -> None:
        for name in ("id", "source", "folder", "data_class"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"SyncAsset.{name} must be a non-empty string")


@dataclass(frozen=True)
class SyncSpec:
    """A manifest's declared sync surface (public shape)."""

    scope: str
    assets: tuple[SyncAsset, ...] = field(default_factory=tuple)
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not isinstance(self.scope, str) or not self.scope.strip():
            raise ValueError("SyncSpec.scope must be a non-empty string")
        seen: set[str] = set()
        for asset in self.assets:
            if asset.id in seen:
                raise ValueError(f"duplicate SyncAsset id: {asset.id!r}")
            seen.add(asset.id)

    @property
    def folders(self) -> frozenset[str]:
        """The distinct folder names this spec references."""
        return frozenset(a.folder for a in self.assets)

    def resolve(self, binding: "SyncBinding") -> tuple["ResolvedAsset", ...]:
        """Join this spec against a private binding into a transport plan.

        Raises :class:`UnboundFolderError` if any asset references a folder the
        binding does not define — the spec and binding must agree.
        """
        resolved: list[ResolvedAsset] = []
        for asset in self.assets:
            fb = binding.folders.get(asset.folder)
            if fb is None:
                raise UnboundFolderError(asset.folder, asset.id)
            resolved.append(ResolvedAsset(asset=asset, binding=fb))
        return tuple(resolved)


@dataclass(frozen=True)
class FolderBinding:
    """Concrete transport target for a named folder (private binding)."""

    name: str
    path: str
    devices: tuple[str, ...] = field(default_factory=tuple)
    syncthing_folder_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("FolderBinding.name must be a non-empty string")
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("FolderBinding.path must be a non-empty string")


@dataclass(frozen=True)
class SyncBinding:
    """The private folder-name → concrete-target map."""

    folders: dict[str, FolderBinding] = field(default_factory=dict)
    schema_version: str = "1.0"


@dataclass(frozen=True)
class ResolvedAsset:
    """A spec asset joined to its concrete folder binding."""

    asset: SyncAsset
    binding: FolderBinding


class UnboundFolderError(KeyError):
    """A spec asset references a folder name absent from the binding."""

    def __init__(self, folder: str, asset_id: str) -> None:
        self.folder = folder
        self.asset_id = asset_id
        super().__init__(
            f"asset {asset_id!r} references folder {folder!r}, which the binding does not define"
        )
