"""Unit tests for cronwatch.trend_checker."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock

import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import HistoryStore
from cronwatch.baseline import Baseline, BaselineStats
from cronwatch.trend_checker import TrendChecker


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def config(tmp_path):
    jobs = [
        JobConfig(name="alpha", schedule="0 * * * *", command="echo alpha"),
        JobConfig(name="beta", schedule="*/5 * * * *", command="echo beta"),
    ]
    return CronwatchConfig(
        jobs=jobs,
        alerts=AlertConfig(webhook_url=None, email=None),
    )


@pytest.fixture
def store(tmp_path):
    return HistoryStore(path=str(tmp_path / "history.json"))


@pytest.fixture
def baseline(tmp_path):
    return Baseline(path=str(tmp_path / "baseline.json"))


@pytest.fixture
def checker(config, store, baseline):
    return TrendChecker(config=config, store=store, baseline=baseline, window=10)


def _add_entries(store: HistoryStore, job_name: str, durations: List[float], failed: int = 0):
    from cronwatch.history import HistoryEntry
    for i, d in enumerate(durations):
        entry = HistoryEntry(
            job_name=job_name,
            started_at=_utc(2024, 1, 1, 0, i % 60),
            finished_at=_utc(2024, 1, 1, 0, i % 60),
            duration=d,
            exit_code=1 if i < failed else 0,
            succeeded=i >= failed,
        )
        store.record(entry)


def test_check_all_returns_result_per_job(checker, store):
    _add_entries(store, "alpha", [30.0] * 5)
    _add_entries(store, "beta", [15.0] * 5)
    results = checker.check_all()
    assert len(results) == 2
    names = {r.job_name for r in results}
    assert names == {"alpha", "beta"}


def test_check_job_stable_flat_durations(checker, store):
    _add_entries(store, "alpha", [30.0] * 8)
    result = checker.check_job("alpha")
    assert result.direction == "stable"


def test_check_job_degrading_on_steep_slope(checker, store):
    _add_entries(store, "alpha", [float(i * 12) for i in range(10)])
    result = checker.check_job("alpha")
    assert result.direction == "degrading"


def test_degrading_property_filters_correctly(checker, store):
    _add_entries(store, "alpha", [float(i * 12) for i in range(10)])
    _add_entries(store, "beta", [20.0] * 10)
    checker.check_all()
    assert len(checker.degrading) == 1
    assert checker.degrading[0].job_name == "alpha"


def test_unknown_direction_for_empty_history(checker):
    result = checker.check_job("alpha")
    assert result.direction == "unknown"
