"""Tests for cronwatch.alert_classifier_runner."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from cronwatch.alert_classifier import Severity
from cronwatch.alert_classifier_runner import AlertClassifierRunner
from cronwatch.baseline import BaselineStats
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import HistoryEntry, HistoryStore


def _utc():
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


def _make_entry(job_name, succeeded=True):
    return HistoryEntry(
        job_name=job_name,
        started_at=_utc(),
        finished_at=_utc(),
        exit_code=0 if succeeded else 1,
        succeeded=succeeded,
    )


@pytest.fixture()
def config():
    return CronwatchConfig(
        jobs=[
            JobConfig(name="alpha", schedule="@hourly", command="echo alpha"),
            JobConfig(name="beta", schedule="@daily", command="echo beta"),
        ],
        alerts=AlertConfig(),
    )


@pytest.fixture()
def store():
    s = MagicMock(spec=HistoryStore)
    s.last.side_effect = lambda name: _make_entry(name, succeeded=(name == "alpha"))
    return s


@pytest.fixture()
def baseline():
    b = MagicMock()
    b.stats_for.return_value = None
    return b


@pytest.fixture()
def checkpoints():
    c = MagicMock()
    c.consecutive_failures.return_value = 0
    return c


@pytest.fixture()
def runner(config, store, baseline, checkpoints):
    r = AlertClassifierRunner(config, store, baseline, checkpoints)
    r.run()
    return r


def test_results_keyed_by_job_name(runner):
    assert set(runner.results.keys()) == {"alpha", "beta"}


def test_actionable_returns_only_high_and_critical(runner):
    actionable = runner.actionable()
    # beta failed → at least MEDIUM; alpha succeeded → LOW
    names = {r.job_name for r in actionable}
    # alpha is healthy → LOW → not actionable
    assert "alpha" not in names


def test_by_severity_filters_correctly(runner):
    low = runner.by_severity(Severity.LOW)
    assert all(r.severity == Severity.LOW for r in low)


def test_run_skips_jobs_with_no_history(config, baseline, checkpoints):
    store = MagicMock(spec=HistoryStore)
    store.last.return_value = None  # no history for any job
    r = AlertClassifierRunner(config, store, baseline, checkpoints)
    r.run()
    assert r.results == {}


def test_consecutive_failures_raises_severity(config, store, baseline):
    cp = MagicMock()
    cp.consecutive_failures.side_effect = lambda name: 6 if name == "beta" else 0
    r = AlertClassifierRunner(config, store, baseline, cp)
    r.run()
    assert r.results["beta"].severity == Severity.CRITICAL
