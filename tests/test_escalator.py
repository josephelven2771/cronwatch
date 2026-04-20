"""Tests for cronwatch.escalator."""
from datetime import datetime, timedelta

import pytest

from cronwatch.escalator import Escalator, EscalationPolicy


@pytest.fixture()
def policy() -> EscalationPolicy:
    return EscalationPolicy(threshold=3, cooldown_minutes=60)


@pytest.fixture()
def escalator(policy: EscalationPolicy) -> Escalator:
    return Escalator(policy)


def test_not_escalated_before_threshold(escalator: Escalator) -> None:
    escalator.record_failure("backup", now=datetime(2024, 1, 1, 12, 0))
    escalator.record_failure("backup", now=datetime(2024, 1, 1, 12, 1))
    assert not escalator.is_escalated("backup")


def test_escalated_at_threshold(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 12, 0)
    for i in range(3):
        result = escalator.record_failure("backup", now=t + timedelta(minutes=i))
    assert result.escalated
    assert escalator.is_escalated("backup")


def test_escalation_result_fields(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 9, 0)
    for i in range(3):
        result = escalator.record_failure("nightly", now=t + timedelta(minutes=i))
    assert result.job_name == "nightly"
    assert result.consecutive_failures == 3
    assert result.escalated_since == t + timedelta(minutes=2)


def test_success_before_cooldown_does_not_deescalate(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 8, 0)
    for i in range(3):
        escalator.record_failure("sync", now=t + timedelta(minutes=i))
    # success arrives only 10 min later — cooldown is 60 min
    escalator.record_success("sync", now=t + timedelta(minutes=10))
    assert escalator.is_escalated("sync")


def test_success_after_cooldown_deescalates(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 8, 0)
    for i in range(3):
        escalator.record_failure("sync", now=t + timedelta(minutes=i))
    escalator.record_success("sync", now=t + timedelta(hours=2))
    assert not escalator.is_escalated("sync")


def test_reset_clears_state(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 8, 0)
    for i in range(5):
        escalator.record_failure("job", now=t + timedelta(minutes=i))
    escalator.reset("job")
    assert not escalator.is_escalated("job")


def test_bool_on_result(escalator: Escalator) -> None:
    t = datetime(2024, 1, 1, 8, 0)
    result = escalator.record_failure("x", now=t)
    assert not bool(result)
    escalator.record_failure("x", now=t + timedelta(minutes=1))
    result = escalator.record_failure("x", now=t + timedelta(minutes=2))
    assert bool(result)


def test_unknown_job_not_escalated(escalator: Escalator) -> None:
    assert not escalator.is_escalated("does-not-exist")
