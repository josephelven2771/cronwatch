"""Tests for cronwatch.escalation_store."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cronwatch.escalator import Escalator, EscalationPolicy
from cronwatch.escalation_store import save_escalator, load_escalator


@pytest.fixture()
def policy() -> EscalationPolicy:
    return EscalationPolicy(threshold=2, cooldown_minutes=30)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "escalation.json"


def _make_escalated(policy: EscalationPolicy) -> Escalator:
    esc = Escalator(policy)
    t = datetime(2024, 6, 1, 10, 0)
    esc.record_failure("job-a", now=t)
    esc.record_failure("job-a", now=t + timedelta(minutes=1))
    return esc


def test_save_creates_file(policy: EscalationPolicy, state_path: Path) -> None:
    esc = _make_escalated(policy)
    save_escalator(esc, state_path)
    assert state_path.exists()


def test_round_trip_preserves_failure_count(policy: EscalationPolicy, state_path: Path) -> None:
    esc = _make_escalated(policy)
    save_escalator(esc, state_path)
    loaded = load_escalator(policy, state_path)
    assert loaded._states["job-a"].consecutive_failures == 2


def test_round_trip_preserves_escalated_since(policy: EscalationPolicy, state_path: Path) -> None:
    esc = _make_escalated(policy)
    save_escalator(esc, state_path)
    loaded = load_escalator(policy, state_path)
    assert loaded.is_escalated("job-a")


def test_load_missing_file_returns_fresh_escalator(policy: EscalationPolicy, state_path: Path) -> None:
    loaded = load_escalator(policy, state_path)
    assert not loaded.is_escalated("job-a")


def test_non_escalated_job_preserved(policy: EscalationPolicy, state_path: Path) -> None:
    esc = Escalator(policy)
    t = datetime(2024, 6, 1, 10, 0)
    esc.record_failure("job-b", now=t)  # only 1 failure, below threshold
    save_escalator(esc, state_path)
    loaded = load_escalator(policy, state_path)
    assert loaded._states["job-b"].consecutive_failures == 1
    assert not loaded.is_escalated("job-b")


def test_multiple_jobs_round_trip(policy: EscalationPolicy, state_path: Path) -> None:
    esc = _make_escalated(policy)
    t = datetime(2024, 6, 1, 10, 0)
    esc.record_failure("job-c", now=t)
    save_escalator(esc, state_path)
    loaded = load_escalator(policy, state_path)
    assert "job-a" in loaded._states
    assert "job-c" in loaded._states
