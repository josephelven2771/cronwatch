"""Unit tests for cronwatch.threshold_checker."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.baseline import Baseline, BaselineStats
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.threshold import ThresholdPolicy
from cronwatch.threshold_checker import ThresholdChecker


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _make_config(*names: str) -> CronwatchConfig:
    jobs = [JobConfig(name=n, schedule="@hourly", command=f"run {n}") for n in names]
    return CronwatchConfig(
        jobs=jobs,
        alerts=AlertConfig(webhook_url=None, email=None),
    )


@pytest.fixture
def config() -> CronwatchConfig:
    return _make_config("alpha", "beta")


@pytest.fixture
def baseline() -> Baseline:
    bl = MagicMock(spec=Baseline)

    def _stats(name):
        if name == "alpha":
            # high failure rate → breach
            return BaselineStats(
                job_name="alpha",
                run_count=10,
                failure_count=8,
                total_duration=200.0,
            )
        # beta: healthy
        return BaselineStats(
            job_name="beta",
            run_count=10,
            failure_count=0,
            total_duration=100.0,
        )

    bl.stats_for.side_effect = _stats
    return bl


@pytest.fixture
def checker(config, baseline) -> ThresholdChecker:
    policy = ThresholdPolicy(max_failure_rate=0.3, max_avg_duration=None, min_runs=3)
    return ThresholdChecker(config, baseline, policy)


# ---------------------------------------------------------------------------

def test_check_all_returns_one_result_per_job(checker):
    results = checker.check_all()
    assert len(results) == 2


def test_check_all_identifies_breach(checker):
    results = checker.check_all()
    breached_names = {r.job_name for r in results if r.breached}
    assert "alpha" in breached_names


def test_check_all_healthy_job_not_breached(checker):
    results = checker.check_all()
    beta = next(r for r in results if r.job_name == "beta")
    assert not beta.breached


def test_breaches_property_filters_correctly(checker):
    checker.check_all()
    assert len(checker.breaches) == 1
    assert checker.breaches[0].job_name == "alpha"


def test_check_job_single(checker):
    result = checker.check_job("alpha")
    assert result.breached


def test_breaches_empty_before_any_check(checker):
    assert checker.breaches == []
