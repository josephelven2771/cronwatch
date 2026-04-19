"""Tests for cronwatch.deduplicator."""
from datetime import datetime, timedelta
import pytest

from cronwatch.deduplicator import Deduplicator


@pytest.fixture
def dedup():
    return Deduplicator(window_seconds=300)


def _now():
    return datetime(2024, 1, 1, 12, 0, 0)


def test_not_duplicate_before_record(dedup):
    assert dedup.is_duplicate("backup", "missed", now=_now()) is False


def test_duplicate_after_record(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    assert dedup.is_duplicate("backup", "missed", now=now) is True


def test_not_duplicate_after_window_expires(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    later = now + timedelta(seconds=301)
    assert dedup.is_duplicate("backup", "missed", now=later) is False


def test_duplicate_within_window(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    soon = now + timedelta(seconds=299)
    assert dedup.is_duplicate("backup", "missed", now=soon) is True


def test_different_reason_not_duplicate(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    assert dedup.is_duplicate("backup", "failed", now=now) is False


def test_different_job_not_duplicate(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    assert dedup.is_duplicate("sync", "missed", now=now) is False


def test_reset_clears_entry(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    dedup.reset("backup", "missed")
    assert dedup.is_duplicate("backup", "missed", now=now) is False


def test_clear_expired_removes_old(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    dedup.record("sync", "failed", now=now)
    later = now + timedelta(seconds=400)
    removed = dedup.clear_expired(now=later)
    assert removed == 2
    assert dedup.is_duplicate("backup", "missed", now=later) is False


def test_clear_expired_keeps_recent(dedup):
    now = _now()
    dedup.record("backup", "missed", now=now)
    later = now + timedelta(seconds=100)
    removed = dedup.clear_expired(now=later)
    assert removed == 0
