"""Tests for cronwatch.incident_store."""
from pathlib import Path

import pytest

from cronwatch.incident import IncidentTracker
from cronwatch.incident_store import save_incidents, load_incidents


@pytest.fixture
def state_path(tmp_path) -> Path:
    return tmp_path / "incidents.ndjson"


@pytest.fixture
def populated_tracker() -> IncidentTracker:
    t = IncidentTracker()
    t.open_or_update("job-a")
    t.open_or_update("job-a")  # failure_count == 2
    t.open_or_update("job-b")
    t.resolve("job-b")
    return t


def test_save_creates_file(state_path, populated_tracker):
    save_incidents(populated_tracker, state_path)
    assert state_path.exists()


def test_save_writes_one_line_per_job(state_path, populated_tracker):
    save_incidents(populated_tracker, state_path)
    lines = [l for l in state_path.read_text().splitlines() if l.strip()]
    assert len(lines) == 2


def test_round_trip_preserves_failure_count(state_path, populated_tracker):
    save_incidents(populated_tracker, state_path)
    loaded = load_incidents(state_path)
    inc = loaded.get("job-a")
    assert inc is not None
    assert inc.failure_count == 2


def test_round_trip_preserves_resolved_status(state_path, populated_tracker):
    save_incidents(populated_tracker, state_path)
    loaded = load_incidents(state_path)
    inc_b = loaded.get("job-b")
    assert inc_b is not None
    assert not inc_b.is_open


def test_load_missing_file_returns_empty_tracker(state_path):
    tracker = load_incidents(state_path)
    assert tracker.all_incidents() == []


def test_save_creates_parent_dirs(tmp_path):
    deep_path = tmp_path / "a" / "b" / "incidents.ndjson"
    t = IncidentTracker()
    t.open_or_update("job-z")
    save_incidents(t, deep_path)
    assert deep_path.exists()
