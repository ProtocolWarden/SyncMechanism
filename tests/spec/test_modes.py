# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for the SyncMode vocabulary."""

import pytest

from sync_mechanism.spec.modes import SyncMode


def test_wire_values_are_stable():
    assert SyncMode.COPY.value == "copy"
    assert SyncMode.IN_REPO.value == "in-repo"
    assert SyncMode.EXTERNAL.value == "external"


def test_str_renders_wire_value():
    assert str(SyncMode.COPY) == "copy"
    assert str(SyncMode.IN_REPO) == "in-repo"


def test_from_value_round_trips():
    for mode in SyncMode:
        assert SyncMode.from_value(mode.value) is mode


def test_from_value_rejects_unknown_with_legal_list():
    with pytest.raises(ValueError) as exc:
        SyncMode.from_value("rsync")
    msg = str(exc.value)
    assert "rsync" in msg
    assert "copy" in msg and "in-repo" in msg and "external" in msg
