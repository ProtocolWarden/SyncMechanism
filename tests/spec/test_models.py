# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for the sync-spec data model and resolution."""

import pytest

from sync_mechanism.spec.models import (
    FolderBinding,
    ResolvedAsset,
    SyncAsset,
    SyncBinding,
    SyncSpec,
    UnboundFolderError,
)
from sync_mechanism.spec.modes import SyncMode


def _asset(**kw):
    base = dict(id="a1", source="repo/state", folder="f1", data_class="operational")
    base.update(kw)
    return SyncAsset(**base)


def test_asset_requires_non_empty_fields():
    for bad in ("id", "source", "folder", "data_class"):
        with pytest.raises(ValueError):
            _asset(**{bad: "  "})


def test_asset_mode_optional_default_none():
    assert _asset().mode is None
    assert _asset(mode=SyncMode.COPY).mode is SyncMode.COPY


def test_spec_requires_scope():
    with pytest.raises(ValueError):
        SyncSpec(scope="")


def test_spec_rejects_duplicate_asset_ids():
    with pytest.raises(ValueError):
        SyncSpec(scope="M", assets=(_asset(id="dup"), _asset(id="dup", folder="f2")))


def test_spec_folders_is_distinct_set():
    spec = SyncSpec(
        scope="M",
        assets=(_asset(id="a", folder="x"), _asset(id="b", folder="x"), _asset(id="c", folder="y")),
    )
    assert spec.folders == frozenset({"x", "y"})


def test_resolve_joins_assets_to_folder_bindings():
    spec = SyncSpec(scope="M", assets=(_asset(id="a", folder="cfg", mode=SyncMode.COPY),))
    binding = SyncBinding(
        folders={"cfg": FolderBinding(name="cfg", path="~/sync/cfg", devices=("p1", "p2"))}
    )
    resolved = spec.resolve(binding)
    assert len(resolved) == 1
    assert isinstance(resolved[0], ResolvedAsset)
    assert resolved[0].asset.id == "a"
    assert resolved[0].binding.path == "~/sync/cfg"
    assert resolved[0].binding.devices == ("p1", "p2")


def test_resolve_raises_on_unbound_folder():
    spec = SyncSpec(scope="M", assets=(_asset(id="a", folder="missing"),))
    with pytest.raises(UnboundFolderError) as exc:
        spec.resolve(SyncBinding(folders={}))
    assert exc.value.folder == "missing"
    assert exc.value.asset_id == "a"


def test_folder_binding_requires_name_and_path():
    with pytest.raises(ValueError):
        FolderBinding(name="", path="/p")
    with pytest.raises(ValueError):
        FolderBinding(name="f", path="")
