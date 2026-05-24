# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Tests for coverage analysis — gap and binding-consistency detection."""

from sync_mechanism.spec.coverage import CoverageReport, coverage_report
from sync_mechanism.spec.models import FolderBinding, SyncAsset, SyncBinding, SyncSpec
from sync_mechanism.spec.modes import SyncMode


def _spec():
    return SyncSpec(
        scope="M",
        assets=(
            SyncAsset(id="covered", source="s", folder="cfg", mode=SyncMode.COPY),
            SyncAsset(id="gap", source="s2", folder="cfg"),  # no mode
        ),
    )


def test_reports_mode_gaps():
    report = coverage_report(_spec())
    assert isinstance(report, CoverageReport)
    assert report.total == 2
    assert report.covered == ("covered",)
    assert report.gaps == ("gap",)
    assert report.is_clean is False  # a gap means not clean


def test_clean_when_all_modes_present_and_no_binding():
    spec = SyncSpec(
        scope="M", assets=(SyncAsset(id="a", source="s", folder="f", mode=SyncMode.IN_REPO),)
    )
    assert coverage_report(spec).is_clean is True


def test_detects_unbound_and_unused_folders():
    spec = SyncSpec(
        scope="M",
        assets=(
            SyncAsset(id="a", source="s", folder="present", mode=SyncMode.COPY),
            SyncAsset(id="b", source="s2", folder="missing", mode=SyncMode.COPY),
        ),
    )
    binding = SyncBinding(
        folders={
            "present": FolderBinding(name="present", path="/p"),
            "orphan": FolderBinding(name="orphan", path="/o"),
        }
    )
    report = coverage_report(spec, binding)
    assert report.unbound_folders == ("missing",)
    assert report.unused_folders == ("orphan",)
    assert report.is_clean is False  # unbound folder


def test_clean_with_consistent_binding():
    spec = SyncSpec(
        scope="M", assets=(SyncAsset(id="a", source="s", folder="f", mode=SyncMode.COPY),)
    )
    binding = SyncBinding(folders={"f": FolderBinding(name="f", path="/p")})
    report = coverage_report(spec, binding)
    assert report.is_clean is True
    assert report.unbound_folders == ()
    assert report.unused_folders == ()
