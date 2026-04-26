"""Tests for cronwatch.alert_dampener."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.alert_dampener import AlertDampener, DampenResult


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


@pytest.fixture()
def dampener() -> AlertDampener:
    return AlertDampener(stable_window=timedelta(minutes=5), flap_threshold=3)


# ---------------------------------------------------------------------------
# DampenResult bool contract
# ---------------------------------------------------------------------------

def test_dampen_result_bool_true_when_not_dampened():
    r = DampenResult(job_name="j", dampened=False, flap_count=0, reason="stable")
    assert bool(r) is True


def test_dampen_result_bool_false_when_dampened():
    r = DampenResult(job_name="j", dampened=True, flap_count=4, reason="flapping")
    assert bool(r) is False


# ---------------------------------------------------------------------------
# No history → not dampened
# ---------------------------------------------------------------------------

def test_check_unknown_job_not_dampened(dampener):
    result = dampener.check("backup")
    assert result.dampened is False
    assert result.flap_count == 0


# ---------------------------------------------------------------------------
# Stable job → not dampened
# ---------------------------------------------------------------------------

def test_stable_failing_job_not_dampened(dampener):
    with patch("cronwatch.alert_dampener._utcnow", side_effect=[_utc(0)] * 10):
        for _ in range(5):
            dampener.record("db-backup", healthy=False)
        result = dampener.check("db-backup")
    assert result.dampened is False


# ---------------------------------------------------------------------------
# Flapping job → dampened once threshold reached
# ---------------------------------------------------------------------------

def test_flapping_job_dampened_at_threshold():
    dampener = AlertDampener(stable_window=timedelta(minutes=5), flap_threshold=3)
    times = [_utc(i * 30) for i in range(20)]
    idx = 0

    def fake_now():
        nonlocal idx
        t = times[idx]
        idx += 1
        return t

    with patch("cronwatch.alert_dampener._utcnow", side_effect=fake_now):
        # Alternate healthy/failing to trigger transitions
        for i in range(7):
            dampener.record("api-sync", healthy=(i % 2 == 0))
        result = dampener.check("api-sync")

    assert result.dampened is True
    assert result.flap_count >= 3


# ---------------------------------------------------------------------------
# Old transitions are pruned; job becomes stable again
# ---------------------------------------------------------------------------

def test_old_transitions_pruned_and_job_recovers():
    dampener = AlertDampener(stable_window=timedelta(minutes=5), flap_threshold=3)

    # Record several flaps far in the past
    old_time = _utc(-600)  # 10 minutes ago — outside 5-min window
    record_times = [old_time] * 10
    # check() is called at 'now' (offset 0)
    check_time = _utc(0)

    call_seq = record_times + [check_time]
    idx = 0

    def fake_now():
        nonlocal idx
        t = call_seq[min(idx, len(call_seq) - 1)]
        idx += 1
        return t

    with patch("cronwatch.alert_dampener._utcnow", side_effect=fake_now):
        for i in range(8):
            dampener.record("etl", healthy=(i % 2 == 0))
        result = dampener.check("etl")

    # All transitions are outside the window → pruned → not dampened
    assert result.dampened is False


# ---------------------------------------------------------------------------
# reason field reflects outcome
# ---------------------------------------------------------------------------

def test_reason_stable_when_not_dampened(dampener):
    dampener.record("heartbeat", healthy=True)
    result = dampener.check("heartbeat")
    assert result.reason == "stable"


def test_reason_contains_flapping_when_dampened():
    dampener = AlertDampener(stable_window=timedelta(minutes=5), flap_threshold=2)
    times = [_utc(i * 10) for i in range(20)]
    idx = 0

    def fake_now():
        nonlocal idx
        t = times[idx]
        idx += 1
        return t

    with patch("cronwatch.alert_dampener._utcnow", side_effect=fake_now):
        for i in range(6):
            dampener.record("worker", healthy=(i % 2 == 0))
        result = dampener.check("worker")

    assert "flapping" in result.reason
