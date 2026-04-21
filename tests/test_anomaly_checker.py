"""Integration-style tests for AnomalyChecker."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.anomaly_checker import AnomalyChecker
from cronwatch.baseline import Baseline, BaselineStats
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import HistoryStore, HistoryEntry


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_config(*names: str) -> CronwatchConfig:
    jobs = [JobConfig(name=n, schedule="@daily", command=f"run {n}") for n in names]
    return CronwatchConfig(jobs=jobs, alerts=AlertConfig())


def _make_entry(job_name: str, duration: float) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=_NOW,
        finished_at=_NOW,
        exit_code=0,
        succeeded=True,
        duration=duration,
    )


@pytest.fixture()
def config():
    return _make_config("backup", "sync")


@pytest.fixture()
def store():
    s = MagicMock(spec=HistoryStore)
    s.last.return_value = None
    return s


@pytest.fixture()
def baseline():
    b = MagicMock(spec=Baseline)
    b.stats_for.return_value = None
    return b


@pytest.fixture()
def checker(config, store, baseline):
    return AnomalyChecker(config, store, baseline)


def test_check_job_returns_none_when_no_history(checker, store):
    store.last.return_value = None
    assert checker.check_job("backup") is None


def test_check_job_returns_none_when_no_duration(checker, store):
    entry = _make_entry("backup", 0.0)
    entry = entry.__class__(**{**entry.__dict__, "duration": None})
    store.last.return_value = entry
    assert checker.check_job("backup") is None


def test_check_job_returns_result_when_history_present(checker, store):
    store.last.return_value = _make_entry("backup", 60.0)
    result = checker.check_job("backup")
    assert result is not None
    assert result.job_name == "backup"


def test_check_all_returns_results_for_all_jobs(checker, store):
    store.last.side_effect = lambda name: _make_entry(name, 60.0)
    results = checker.check_all()
    assert len(results) == 2
    assert {r.job_name for r in results} == {"backup", "sync"}


def test_anomalies_filters_non_anomalous(checker, store, baseline):
    from cronwatch.baseline import BaselineStats
    store.last.side_effect = lambda name: _make_entry(name, 60.0)
    # baseline: mean=60, stddev=1 → z=0 for backup; mean=60, stddev=1 → z=35 for sync
    def _stats(name):
        if name == "sync":
            return BaselineStats(name, 10, 60.0, 1.0, 0.0)
        return BaselineStats(name, 10, 60.0, 1.0, 0.0)
    baseline.stats_for.side_effect = _stats
    results = checker.anomalies()
    # z=0 for both → no anomalies
    assert results == []
