# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Load and validate sync-spec / sync-binding documents from YAML.

The on-disk format is deliberately small and declarative. A sync spec:

    schema_version: "1.0"
    scope: PlatformManifest
    assets:
      - id: oc-operational
        data_class: operational
        mode: copy
        source: OperationsCenter/state
        folder: oc-config
      - id: oc-plane-backups          # declared but mode omitted = coverage gap
        data_class: operational
        source: ~/plane-backups
        folder: platform-backups

A binding (private layer) maps folder names to concrete targets:

    schema_version: "1.0"
    folders:
      oc-config:
        path: ~/sync/platform/config
        devices: [primary, secondary]
        syncthing_folder_id: oc-config
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import FolderBinding, SyncAsset, SyncBinding, SyncSpec
from .modes import SyncMode


class SpecParseError(ValueError):
    """A sync-spec or binding document is malformed."""


def _require_mapping(data: Any, what: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SpecParseError(f"{what} must be a mapping, got {type(data).__name__}")
    return data


def parse_spec(data: Any) -> SyncSpec:
    """Build a :class:`SyncSpec` from already-parsed YAML/JSON data."""
    doc = _require_mapping(data, "sync spec")
    raw_assets = doc.get("assets") or []
    if not isinstance(raw_assets, list):
        raise SpecParseError("sync spec 'assets' must be a list")
    assets: list[SyncAsset] = []
    for i, raw in enumerate(raw_assets):
        item = _require_mapping(raw, f"assets[{i}]")
        mode_value = item.get("mode")
        try:
            mode = SyncMode.from_value(mode_value) if mode_value is not None else None
        except ValueError as exc:
            raise SpecParseError(f"assets[{i}]: {exc}") from exc
        try:
            assets.append(
                SyncAsset(
                    id=item.get("id", ""),
                    source=item.get("source", ""),
                    folder=item.get("folder", ""),
                    data_class=item.get("data_class", "operational"),
                    mode=mode,
                )
            )
        except ValueError as exc:
            raise SpecParseError(f"assets[{i}]: {exc}") from exc
    try:
        return SyncSpec(
            scope=doc.get("scope", ""),
            assets=tuple(assets),
            schema_version=str(doc.get("schema_version", "1.0")),
        )
    except ValueError as exc:
        raise SpecParseError(str(exc)) from exc


def parse_binding(data: Any) -> SyncBinding:
    """Build a :class:`SyncBinding` from already-parsed YAML/JSON data."""
    doc = _require_mapping(data, "sync binding")
    raw_folders = doc.get("folders") or {}
    raw_folders = _require_mapping(raw_folders, "binding 'folders'")
    folders: dict[str, FolderBinding] = {}
    for name, raw in raw_folders.items():
        item = _require_mapping(raw, f"folders[{name!r}]")
        devices = item.get("devices") or []
        if not isinstance(devices, list):
            raise SpecParseError(f"folders[{name!r}].devices must be a list")
        try:
            folders[name] = FolderBinding(
                name=name,
                path=item.get("path", ""),
                devices=tuple(str(d) for d in devices),
                syncthing_folder_id=item.get("syncthing_folder_id"),
            )
        except ValueError as exc:
            raise SpecParseError(f"folders[{name!r}]: {exc}") from exc
    return SyncBinding(
        folders=folders,
        schema_version=str(doc.get("schema_version", "1.0")),
    )


def _load_yaml(path: str | Path) -> Any:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecParseError(f"cannot read {p}: {exc}") from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SpecParseError(f"invalid YAML in {p}: {exc}") from exc


def load_spec(path: str | Path) -> SyncSpec:
    """Load and validate a sync spec from a YAML file."""
    return parse_spec(_load_yaml(path))


def load_binding(path: str | Path) -> SyncBinding:
    """Load and validate a sync binding from a YAML file."""
    return parse_binding(_load_yaml(path))
