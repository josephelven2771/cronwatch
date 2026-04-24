"""Tests for cronwatch.alert_suppressor."""
from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.alert_suppressor import AlertSuppressor, SuppressionResult
from cronwatch.silencer import Silencer, SilenceWindow
from cronwatch.cooldown import CooldownTracker
from cronwatch.deduplicator import Deduplicator


def _utc(offset_seconds: float = 0.0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


@pytest.fixture
def suppressor() -> AlertSuppressor:
    silencer = Silencer()
    cooldown = CooldownTracker(window_seconds=300)
    dedup = Deduplicator(window_seconds=60)
    return AlertSuppressor(silencer=silencer, cooldown=cooldown, deduplicator=dedup)


def test_check_allowed_by_default(suppressor):
    result = suppressor.check("backup", "job failed", now=_utc())
    assert result.allowed is True
    assert result.reason == "allowed"


def test_bool_true_when_allowed(suppressor):
    result = suppressor.check("backup", "job failed", now=_utc())
    assert bool(result) is True


def test_suppressed_when_silenced(suppressor):
    window = SilenceWindow(
        start=_utc(-60),
        end=_utc(3600),
        job_name="backup",
    )
    suppressor.silencer.add(window)
    result = suppressor.check("backup", "job failed", now=_utc())
    assert result.allowed is False
    assert result.reason == "silenced"


def test_suppressed_when_in_cooldown(suppressor):
    now = _utc()
    suppressor.record("backup", "job failed", now=now)
    result = suppressor.check("backup", "job failed", now=_utc(10))
    assert result.allowed is False
    assert result.reason == "cooldown"


def test_allowed_after_cooldown_expires(suppressor):
    now = _utc()
    suppressor.record("backup", "job failed", now=now)
    result = suppressor.check("backup", "job failed", now=_utc(400))
    assert result.allowed is True


def test_suppressed_as_duplicate_same_message(suppressor):
    now = _utc()
    # Use a very short cooldown so cooldown doesn't block
    suppressor.cooldown = CooldownTracker(window_seconds=0)
    suppressor.record("backup", "job failed", now=now)
    result = suppressor.check("backup", "job failed", now=_utc(5))
    assert result.allowed is False
    assert result.reason == "duplicate"


def test_different_message_not_duplicate(suppressor):
    suppressor.cooldown = CooldownTracker(window_seconds=0)
    now = _utc()
    suppressor.record("backup", "job failed", now=now)
    result = suppressor.check("backup", "different error", now=_utc(5))
    assert result.allowed is True


def test_suppressed_count_increments(suppressor):
    window = SilenceWindow(start=_utc(-60), end=_utc(3600), job_name="backup")
    suppressor.silencer.add(window)
    suppressor.check("backup", "msg", now=_utc())
    suppressor.check("backup", "msg", now=_utc())
    assert suppressor.suppressed_count == 2


def test_suppressed_count_not_incremented_when_allowed(suppressor):
    suppressor.check("backup", "msg", now=_utc())
    assert suppressor.suppressed_count == 0
