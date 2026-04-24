"""Tests for cronwatch.alert_throttle."""
from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.alert_throttle import AlertThrottle, ThrottlePolicy, ThrottleResult


def _utc(offset_seconds: float = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )


@pytest.fixture()
def policy() -> ThrottlePolicy:
    return ThrottlePolicy(max_alerts=3, window_seconds=60)


@pytest.fixture()
def throttle(policy: ThrottlePolicy) -> AlertThrottle:
    return AlertThrottle(policy)


def test_check_returns_throttle_result(throttle: AlertThrottle) -> None:
    result = throttle.check("backup", now=_utc())
    assert isinstance(result, ThrottleResult)


def test_initially_allowed(throttle: AlertThrottle) -> None:
    result = throttle.check("backup", now=_utc())
    assert result.allowed is True
    assert bool(result) is True


def test_sent_in_window_zero_initially(throttle: AlertThrottle) -> None:
    result = throttle.check("backup", now=_utc())
    assert result.sent_in_window == 0


def test_record_increments_count(throttle: AlertThrottle) -> None:
    throttle.record("backup", now=_utc())
    result = throttle.check("backup", now=_utc(1))
    assert result.sent_in_window == 1


def test_blocked_after_max_alerts(throttle: AlertThrottle) -> None:
    for i in range(3):
        throttle.record("backup", now=_utc(i))
    result = throttle.check("backup", now=_utc(3))
    assert result.allowed is False
    assert result.sent_in_window == 3
    assert "throttled" in result.reason


def test_allowed_after_window_expires(throttle: AlertThrottle) -> None:
    for i in range(3):
        throttle.record("backup", now=_utc(i))
    # Advance past the 60-second window
    result = throttle.check("backup", now=_utc(120))
    assert result.allowed is True
    assert result.sent_in_window == 0


def test_different_jobs_are_independent(throttle: AlertThrottle) -> None:
    for i in range(3):
        throttle.record("job-a", now=_utc(i))
    result = throttle.check("job-b", now=_utc(3))
    assert result.allowed is True


def test_reset_clears_state(throttle: AlertThrottle) -> None:
    for i in range(3):
        throttle.record("backup", now=_utc(i))
    throttle.reset("backup")
    result = throttle.check("backup", now=_utc(3))
    assert result.allowed is True
    assert result.sent_in_window == 0


def test_result_exposes_max_alerts(throttle: AlertThrottle) -> None:
    result = throttle.check("backup", now=_utc())
    assert result.max_alerts == 3


def test_default_policy_is_applied() -> None:
    t = AlertThrottle()
    result = t.check("x", now=_utc())
    assert result.max_alerts == 5
