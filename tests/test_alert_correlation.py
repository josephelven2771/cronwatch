"""Tests for cronwatch.alert_correlation."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.alert_correlation import AlertCorrelator, CorrelatedEvent
from cronwatch.history import HistoryEntry


def _utc(hour: int = 12, minute: int = 0) -> datetime:
    return datetime(2024, 1, 15, hour, minute, 0, tzinfo=timezone.utc)


def _entry(
    job_name: str,
    succeeded: bool = True,
    started_at: datetime | None = None,
) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=started_at or _utc(),
        finished_at=_utc(12, 1),
        succeeded=succeeded,
        exit_code=0 if succeeded else 1,
        duration=60.0,
    )


@pytest.fixture
def correlator() -> AlertCorrelator:
    return AlertCorrelator(group_by_prefix=True)


def test_add_returns_correlation_key(correlator):
    key = correlator.add(_entry("backup_daily"))
    assert key == "backup"


def test_add_no_prefix_uses_full_name(correlator):
    key = correlator.add(_entry("nightly"))
    assert key == "nightly"


def test_events_groups_by_prefix(correlator):
    correlator.add(_entry("backup_daily"))
    correlator.add(_entry("backup_weekly"))
    correlator.add(_entry("report_daily"))

    events = correlator.events()
    keys = {e.correlation_id for e in events}
    assert keys == {"backup", "report"}


def test_correlated_event_size(correlator):
    correlator.add(_entry("sync_a"))
    correlator.add(_entry("sync_b"))
    events = correlator.events()
    assert len(events) == 1
    assert events[0].size == 2


def test_correlated_event_failure_count(correlator):
    correlator.add(_entry("sync_a", succeeded=True))
    correlator.add(_entry("sync_b", succeeded=False))
    correlator.add(_entry("sync_c", succeeded=False))
    event = correlator.events()[0]
    assert event.failure_count == 2


def test_correlated_event_bool_true(correlator):
    correlator.add(_entry("sync_a"))
    event = correlator.events()[0]
    assert bool(event) is True


def test_correlated_event_bool_false():
    event = CorrelatedEvent(
        correlation_id="empty",
        job_names=[],
        entries=[],
        first_seen=_utc(),
        last_seen=_utc(),
    )
    assert bool(event) is False


def test_correlated_event_summary_contains_id(correlator):
    correlator.add(_entry("sync_a"))
    event = correlator.events()[0]
    assert "sync" in event.summary
    assert "1 events" in event.summary


def test_first_and_last_seen_set_correctly(correlator):
    correlator.add(_entry("sync_a", started_at=_utc(10, 0)))
    correlator.add(_entry("sync_b", started_at=_utc(11, 0)))
    event = correlator.events()[0]
    assert event.first_seen == _utc(10, 0)
    assert event.last_seen == _utc(11, 0)


def test_clear_removes_all_buckets(correlator):
    correlator.add(_entry("sync_a"))
    correlator.clear()
    assert correlator.events() == []


def test_group_by_prefix_false_uses_full_name():
    c = AlertCorrelator(group_by_prefix=False)
    key = c.add(_entry("backup_daily"))
    assert key == "backup_daily"
    assert len(c.events()) == 1
    assert c.events()[0].correlation_id == "backup_daily"
