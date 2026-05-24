# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for loading/parsing sync specs and bindings from YAML."""

import pytest

from sync_mechanism.spec.loader import (
    SpecParseError,
    load_binding,
    load_spec,
    parse_binding,
    parse_spec,
)
from sync_mechanism.spec.modes import SyncMode

_SPEC = {
    "schema_version": "1.0",
    "scope": "PlatformManifest",
    "assets": [
        {"id": "a", "mode": "copy", "source": "r/state", "folder": "cfg"},
        {"id": "b", "source": "r/big", "folder": "media"},  # no mode -> gap
    ],
}

_BINDING = {
    "schema_version": "1.0",
    "folders": {
        "cfg": {"path": "~/sync/cfg", "devices": ["p1", "p2"], "syncthing_folder_id": "cfg"},
        "media": {"path": "~/sync/media"},
    },
}


def test_parse_spec_builds_assets_and_modes():
    spec = parse_spec(_SPEC)
    assert spec.scope == "PlatformManifest"
    assert [a.id for a in spec.assets] == ["a", "b"]
    assert spec.assets[0].mode is SyncMode.COPY
    assert spec.assets[1].mode is None


def test_parse_spec_rejects_unknown_mode():
    bad = {"scope": "M", "assets": [{"id": "a", "mode": "ftp", "source": "s", "folder": "f"}]}
    with pytest.raises(SpecParseError) as exc:
        parse_spec(bad)
    assert "ftp" in str(exc.value)


def test_parse_spec_rejects_non_mapping():
    with pytest.raises(SpecParseError):
        parse_spec([1, 2, 3])


def test_parse_spec_rejects_non_list_assets():
    with pytest.raises(SpecParseError):
        parse_spec({"scope": "M", "assets": {"not": "a list"}})


def test_parse_spec_propagates_missing_required_field():
    with pytest.raises(SpecParseError):
        parse_spec({"scope": "M", "assets": [{"mode": "copy", "source": "s", "folder": "f"}]})


def test_parse_binding_builds_folders():
    binding = parse_binding(_BINDING)
    assert set(binding.folders) == {"cfg", "media"}
    assert binding.folders["cfg"].devices == ("p1", "p2")
    assert binding.folders["media"].devices == ()


def test_parse_binding_rejects_non_list_devices():
    with pytest.raises(SpecParseError):
        parse_binding({"folders": {"f": {"path": "/p", "devices": "p1"}}})


def test_load_spec_and_binding_round_trip(tmp_path):
    import yaml

    spec_path = tmp_path / "spec.yaml"
    bind_path = tmp_path / "binding.yaml"
    spec_path.write_text(yaml.safe_dump(_SPEC), encoding="utf-8")
    bind_path.write_text(yaml.safe_dump(_BINDING), encoding="utf-8")

    spec = load_spec(spec_path)
    binding = load_binding(bind_path)
    assert len(spec.assets) == 2
    assert set(binding.folders) == {"cfg", "media"}


def test_load_spec_reports_missing_file():
    with pytest.raises(SpecParseError):
        load_spec("/nonexistent/path/spec.yaml")


def test_load_spec_reports_bad_yaml(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("scope: [unclosed\n", encoding="utf-8")
    with pytest.raises(SpecParseError):
        load_spec(p)
