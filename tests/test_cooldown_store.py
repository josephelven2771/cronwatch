"""Tests for cronwatch.cooldown_store."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.cooldown import CooldownTracker
from cronwatch.cooldown_store import load_cooldown, save_cooldown


def _utc() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def state_path(tmp_path) -> Path:
    return tmp_path / "cooldown.json"


@pytest.fixture
def populated_tracker() -> CooldownTracker:
    t = CooldownTracker(window_seconds=600)
    t.record_alert("backup", now=_utc())
    t.record_alert("sync", now=_utc())
    return t


def test_save_creates_file(state_path, populated_tracker):
    save_cooldown(populated_tracker, state_path)
    assert state_path.exists()


def test_load_returns_empty_tracker_when_no_file(state_path):
    tracker = load_cooldown(state_path)
    assert tracker.can_alert("any_job") is True


def test_round_trip_preserves_window_seconds(state_path, populated_tracker):
    save_cooldown(populated_tracker, state_path)
    restored = load_cooldown(state_path)
    assert restored.window_seconds == populated_tracker.window_seconds


def test_round_trip_preserves_entries(state_path, populated_tracker):
    save_cooldown(populated_tracker, state_path)
    restored = load_cooldown(state_path)
    assert restored.entry_for("backup") is not None
    assert restored.entry_for("sync") is not None


def test_round_trip_preserves_alert_count(state_path):
    t = CooldownTracker(window_seconds=300)
    now = _utc()
    t.record_alert("job_a", now=now)
    # Simulate a second alert after cooldown
    from datetime import timedelta
    t.record_alert("job_a", now=now + timedelta(seconds=400))
    save_cooldown(t, state_path)
    restored = load_cooldown(state_path)
    assert restored.entry_for("job_a").alert_count == 2


def test_load_uses_fallback_window_when_key_missing(state_path):
    import json
    state_path.write_text(json.dumps({"entries": []}))
    restored = load_cooldown(state_path, window_seconds=120)
    assert restored.window_seconds == 120
