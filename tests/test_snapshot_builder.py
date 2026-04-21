"""Tests for snapshot_builder.py – build_snapshot and diff_snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.config import JobConfig
from cronwatch.snapshot import JobSnapshot, Snapshot
from cronwatch.snapshot_builder import build_snapshot, diff_snapshots


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _make_entry(exit_code: int, started_at: datetime, duration: float = 1.0):
    e = MagicMock()
    e.exit_code = exit_code
    e.started_at = started_at
    e.duration = duration
    return e


@pytest.fixture
def config():
    cfg = MagicMock()
    cfg.jobs = [JobConfig(name="backup", schedule="0 * * * *", command="tar")]
    return cfg


@pytest.fixture
def store():
    return MagicMock()


def test_build_snapshot_no_history(config, store):
    store.get.return_value = []
    snap = build_snapshot(config, store)
    assert "backup" in snap.jobs
    js = snap.jobs["backup"]
    assert js.last_run is None
    assert js.success_count == 0


def test_build_snapshot_with_entries(config, store):
    entries = [
        _make_entry(0, _utc(2024, 6, 1, 9, 0)),
        _make_entry(1, _utc(2024, 6, 1, 10, 0)),
        _make_entry(0, _utc(2024, 6, 1, 11, 0)),
    ]
    store.get.return_value = entries
    snap = build_snapshot(config, store)
    js = snap.jobs["backup"]
    assert js.last_run == _utc(2024, 6, 1, 11, 0)
    assert js.last_exit_code == 0
    assert js.success_count == 2
    assert js.failure_count == 1


def test_diff_snapshots_detects_change():
    before = Snapshot(taken_at=_utc(2024, 6, 1, 10, 0))
    before.jobs["backup"] = JobSnapshot("backup", _utc(2024, 6, 1, 9, 0), 0, 1.0, 5, 0)

    after = Snapshot(taken_at=_utc(2024, 6, 1, 11, 0))
    after.jobs["backup"] = JobSnapshot("backup", _utc(2024, 6, 1, 10, 0), 1, 1.0, 5, 1)

    changes = diff_snapshots(before, after)
    assert "backup" in changes
    assert changes["backup"]["after_exit_code"] == 1


def test_diff_snapshots_no_change():
    ts = _utc(2024, 6, 1, 10, 0)
    before = Snapshot(taken_at=ts)
    before.jobs["backup"] = JobSnapshot("backup", ts, 0, 1.0, 5, 0)
    after = Snapshot(taken_at=ts)
    after.jobs["backup"] = JobSnapshot("backup", ts, 0, 1.0, 5, 0)

    changes = diff_snapshots(before, after)
    assert changes == {}


def test_diff_snapshots_new_job():
    before = Snapshot(taken_at=_utc(2024, 6, 1, 10, 0))
    after = Snapshot(taken_at=_utc(2024, 6, 1, 11, 0))
    after.jobs["newjob"] = JobSnapshot("newjob", _utc(2024, 6, 1, 10, 30), 0, 2.0, 1, 0)

    changes = diff_snapshots(before, after)
    assert "newjob" in changes
