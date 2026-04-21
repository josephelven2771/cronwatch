"""Tests for snapshot.py – data model, serialisation, and persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.snapshot import (
    JobSnapshot,
    Snapshot,
    load_snapshot,
    save_snapshot,
)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def job_snap() -> JobSnapshot:
    return JobSnapshot(
        job_name="backup",
        last_run=_utc(2024, 6, 1, 10, 0, 0),
        last_exit_code=0,
        last_duration=5.3,
        success_count=10,
        failure_count=1,
    )


@pytest.fixture
def snapshot(job_snap) -> Snapshot:
    s = Snapshot(taken_at=_utc(2024, 6, 1, 12, 0, 0))
    s.jobs["backup"] = job_snap
    return s


def test_job_snapshot_is_healthy(job_snap):
    assert job_snap.is_healthy() is True


def test_job_snapshot_not_healthy():
    snap = JobSnapshot("job", None, 1, None, 0, 3)
    assert snap.is_healthy() is False


def test_job_snapshot_round_trip(job_snap):
    restored = JobSnapshot.from_dict(job_snap.to_dict())
    assert restored.job_name == job_snap.job_name
    assert restored.last_run == job_snap.last_run
    assert restored.last_exit_code == job_snap.last_exit_code
    assert restored.success_count == job_snap.success_count


def test_snapshot_round_trip(snapshot):
    restored = Snapshot.from_dict(snapshot.to_dict())
    assert restored.taken_at == snapshot.taken_at
    assert "backup" in restored.jobs
    assert restored.jobs["backup"].failure_count == 1


def test_save_and_load_snapshot(tmp_path, snapshot):
    path = tmp_path / "state" / "snapshot.json"
    save_snapshot(snapshot, path)
    assert path.exists()
    loaded = load_snapshot(path)
    assert loaded is not None
    assert loaded.taken_at == snapshot.taken_at
    assert loaded.jobs["backup"].last_exit_code == 0


def test_load_snapshot_returns_none_when_missing(tmp_path):
    result = load_snapshot(tmp_path / "nonexistent.json")
    assert result is None


def test_snapshot_to_dict_contains_jobs(snapshot):
    d = snapshot.to_dict()
    assert "taken_at" in d
    assert "backup" in d["jobs"]
