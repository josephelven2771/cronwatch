"""Tests for cronwatch.cooldown."""

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.cooldown import CooldownEntry, CooldownTracker


def _utc(offset_seconds: int = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


@pytest.fixture
def tracker() -> CooldownTracker:
    return CooldownTracker(window_seconds=300)


def test_can_alert_when_no_entry(tracker):
    assert tracker.can_alert("backup") is True


def test_cannot_alert_immediately_after_record(tracker):
    now = _utc()
    tracker.record_alert("backup", now=now)
    assert tracker.can_alert("backup", now=now) is False


def test_can_alert_after_window_expires(tracker):
    now = _utc()
    tracker.record_alert("backup", now=now)
    later = _utc(301)
    assert tracker.can_alert("backup", now=later) is True


def test_cannot_alert_just_before_window_expires(tracker):
    now = _utc()
    tracker.record_alert("backup", now=now)
    just_before = _utc(299)
    assert tracker.can_alert("backup", now=just_before) is False


def test_record_alert_increments_count(tracker):
    now = _utc()
    tracker.record_alert("backup", now=now)
    later = _utc(400)
    entry = tracker.record_alert("backup", now=later)
    assert entry.alert_count == 2


def test_reset_clears_entry(tracker):
    tracker.record_alert("backup", now=_utc())
    tracker.reset("backup")
    assert tracker.can_alert("backup") is True
    assert tracker.entry_for("backup") is None


def test_reset_unknown_job_is_noop(tracker):
    tracker.reset("nonexistent")  # should not raise


def test_entry_for_returns_none_when_absent(tracker):
    assert tracker.entry_for("missing") is None


def test_entry_for_returns_entry_after_record(tracker):
    now = _utc()
    tracker.record_alert("cleanup", now=now)
    entry = tracker.entry_for("cleanup")
    assert entry is not None
    assert entry.job_name == "cleanup"
    assert entry.last_alerted == now


def test_cooldown_entry_round_trip():
    now = _utc()
    entry = CooldownEntry(job_name="sync", last_alerted=now, alert_count=3)
    restored = CooldownEntry.from_dict(entry.to_dict())
    assert restored.job_name == entry.job_name
    assert restored.last_alerted == entry.last_alerted
    assert restored.alert_count == entry.alert_count


def test_multiple_jobs_tracked_independently(tracker):
    now = _utc()
    tracker.record_alert("job_a", now=now)
    assert tracker.can_alert("job_b", now=now) is True
    assert tracker.can_alert("job_a", now=now) is False
