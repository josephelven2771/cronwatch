"""Tests for cronwatch.heartbeat."""

import time
from pathlib import Path

import pytest

from cronwatch.heartbeat import HeartbeatRecord, HeartbeatStore


# ---------------------------------------------------------------------------
# HeartbeatRecord unit tests
# ---------------------------------------------------------------------------

def test_record_not_overdue_immediately():
    now = time.time()
    rec = HeartbeatRecord(job_name="nightly", last_ping=now, interval_seconds=3600)
    assert not rec.is_overdue(now=now)


def test_record_overdue_after_interval():
    now = time.time()
    past = now - 7200  # 2 hours ago
    rec = HeartbeatRecord(job_name="nightly", last_ping=past, interval_seconds=3600)
    assert rec.is_overdue(now=now)


def test_seconds_overdue_zero_when_not_overdue():
    now = time.time()
    rec = HeartbeatRecord(job_name="nightly", last_ping=now, interval_seconds=3600)
    assert rec.seconds_overdue(now=now) == 0.0


def test_seconds_overdue_positive_when_overdue():
    now = time.time()
    past = now - 5000
    rec = HeartbeatRecord(job_name="nightly", last_ping=past, interval_seconds=3600)
    assert rec.seconds_overdue(now=now) == pytest.approx(1400.0, abs=1.0)


def test_round_trip_dict():
    now = time.time()
    rec = HeartbeatRecord(job_name="hourly", last_ping=now, interval_seconds=3600)
    restored = HeartbeatRecord.from_dict(rec.to_dict())
    assert restored.job_name == rec.job_name
    assert restored.last_ping == pytest.approx(rec.last_ping)
    assert restored.interval_seconds == rec.interval_seconds


# ---------------------------------------------------------------------------
# HeartbeatStore integration tests
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path: Path) -> HeartbeatStore:
    return HeartbeatStore(tmp_path / "heartbeats.json")


def test_ping_returns_record(store: HeartbeatStore):
    now = time.time()
    rec = store.ping("backup", interval_seconds=600, now=now)
    assert rec.job_name == "backup"
    assert rec.last_ping == pytest.approx(now)


def test_get_returns_none_for_unknown(store: HeartbeatStore):
    assert store.get("ghost") is None


def test_get_returns_record_after_ping(store: HeartbeatStore):
    now = time.time()
    store.ping("cleanup", interval_seconds=1800, now=now)
    rec = store.get("cleanup")
    assert rec is not None
    assert rec.interval_seconds == 1800


def test_all_overdue_empty_when_fresh(store: HeartbeatStore):
    now = time.time()
    store.ping("job_a", interval_seconds=3600, now=now)
    assert store.all_overdue(now=now) == []


def test_all_overdue_detects_stale_jobs(store: HeartbeatStore):
    now = time.time()
    store.ping("stale", interval_seconds=60, now=now - 120)
    store.ping("fresh", interval_seconds=3600, now=now)
    overdue = store.all_overdue(now=now)
    assert len(overdue) == 1
    assert overdue[0].job_name == "stale"


def test_store_persists_across_instances(tmp_path: Path):
    path = tmp_path / "hb.json"
    now = time.time()
    s1 = HeartbeatStore(path)
    s1.ping("persisted", interval_seconds=900, now=now)

    s2 = HeartbeatStore(path)
    rec = s2.get("persisted")
    assert rec is not None
    assert rec.interval_seconds == 900
