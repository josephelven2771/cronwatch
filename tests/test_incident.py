"""Tests for cronwatch.incident."""
from datetime import datetime, timezone

import pytest

from cronwatch.incident import Incident, IncidentTracker


@pytest.fixture
def tracker() -> IncidentTracker:
    return IncidentTracker()


def test_open_creates_new_incident(tracker):
    inc = tracker.open_or_update("job-a")
    assert inc.job_name == "job-a"
    assert inc.is_open
    assert inc.failure_count == 1
    assert inc.incident_id != ""


def test_open_twice_increments_failure_count(tracker):
    tracker.open_or_update("job-a")
    inc = tracker.open_or_update("job-a")
    assert inc.failure_count == 2


def test_open_twice_same_incident_id(tracker):
    first = tracker.open_or_update("job-a")
    second = tracker.open_or_update("job-a")
    assert first.incident_id == second.incident_id


def test_resolve_marks_resolved(tracker):
    tracker.open_or_update("job-a")
    resolved = tracker.resolve("job-a")
    assert resolved is not None
    assert not resolved.is_open
    assert resolved.resolved_at is not None


def test_resolve_unknown_job_returns_none(tracker):
    result = tracker.resolve("no-such-job")
    assert result is None


def test_open_after_resolve_creates_new_incident(tracker):
    first = tracker.open_or_update("job-a")
    tracker.resolve("job-a")
    second = tracker.open_or_update("job-a")
    assert second.incident_id != first.incident_id
    assert second.failure_count == 1


def test_open_incidents_filters_resolved(tracker):
    tracker.open_or_update("job-a")
    tracker.open_or_update("job-b")
    tracker.resolve("job-a")
    open_names = [i.job_name for i in tracker.open_incidents()]
    assert "job-b" in open_names
    assert "job-a" not in open_names


def test_round_trip_to_dict():
    inc = Incident(
        job_name="job-x",
        incident_id="abc-123",
        opened_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        failure_count=3,
    )
    restored = Incident.from_dict(inc.to_dict())
    assert restored.job_name == inc.job_name
    assert restored.incident_id == inc.incident_id
    assert restored.failure_count == inc.failure_count
    assert restored.resolved_at is None
