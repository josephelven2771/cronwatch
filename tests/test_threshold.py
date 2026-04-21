"""Unit tests for cronwatch.threshold."""
from __future__ import annotations

import pytest

from cronwatch.baseline import BaselineStats
from cronwatch.threshold import ThresholdPolicy, ThresholdResult, check_threshold


@pytest.fixture
def policy() -> ThresholdPolicy:
    return ThresholdPolicy(max_failure_rate=0.3, max_avg_duration=60.0, min_runs=3)


def _stats(run_count: int, failure_count: int, total_duration: float) -> BaselineStats:
    return BaselineStats(
        job_name="backup",
        run_count=run_count,
        failure_count=failure_count,
        total_duration=total_duration,
    )


# ---------------------------------------------------------------------------

def test_no_stats_returns_no_breach(policy):
    result = check_threshold("backup", None, policy)
    assert not result.breached
    assert result.failure_rate is None
    assert result.avg_duration is None


def test_too_few_runs_returns_no_breach(policy):
    stats = _stats(run_count=2, failure_count=2, total_duration=200.0)
    result = check_threshold("backup", stats, policy)
    assert not result.breached


def test_healthy_job_no_breach(policy):
    stats = _stats(run_count=10, failure_count=1, total_duration=300.0)
    result = check_threshold("backup", stats, policy)
    assert not result.breached
    assert result.reasons == []


def test_high_failure_rate_causes_breach(policy):
    # 5 failures out of 10 = 50% > 30% limit
    stats = _stats(run_count=10, failure_count=5, total_duration=100.0)
    result = check_threshold("backup", stats, policy)
    assert result.breached
    assert any("failure rate" in r for r in result.reasons)


def test_high_avg_duration_causes_breach(policy):
    # avg = 800 / 10 = 80s > 60s limit, failure rate = 0%
    stats = _stats(run_count=10, failure_count=0, total_duration=800.0)
    result = check_threshold("backup", stats, policy)
    assert result.breached
    assert any("avg duration" in r for r in result.reasons)


def test_both_limits_exceeded_gives_two_reasons(policy):
    stats = _stats(run_count=10, failure_count=5, total_duration=800.0)
    result = check_threshold("backup", stats, policy)
    assert result.breached
    assert len(result.reasons) == 2


def test_bool_true_when_breached(policy):
    stats = _stats(run_count=10, failure_count=8, total_duration=100.0)
    result = check_threshold("backup", stats, policy)
    assert bool(result) is True


def test_bool_false_when_not_breached(policy):
    stats = _stats(run_count=10, failure_count=0, total_duration=100.0)
    result = check_threshold("backup", stats, policy)
    assert bool(result) is False


def test_no_duration_limit_ignores_duration():
    policy = ThresholdPolicy(max_failure_rate=0.5, max_avg_duration=None, min_runs=3)
    stats = _stats(run_count=10, failure_count=0, total_duration=9999.0)
    result = check_threshold("backup", stats, policy)
    assert not result.breached
