"""Tests for cronwatch.alert_correlation_runner."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.alert_correlation_runner import AlertCorrelationRunner
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import HistoryEntry, HistoryStore


def _utc(hour: int = 12) -> datetime:
    return datetime(2024, 1, 15, hour, 0, 0, tzinfo=timezone.utc)


def _make_entry(job_name: str, succeeded: bool = True) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=_utc(),
        finished_at=_utc(13),
        succeeded=succeeded,
        exit_code=0 if succeeded else 1,
        duration=60.0,
    )


def _make_job(name: str) -> JobConfig:
    return JobConfig(name=name, schedule="0 * * * *", command=f"run_{name}")


@pytest.fixture
def config():
    return CronwatchConfig(
        jobs=[
            _make_job("backup_daily"),
            _make_job("backup_weekly"),
            _make_job("report_daily"),
        ],
        alerts=AlertConfig(webhook_url=None, email=None),
    )


@pytest.fixture
def store():
    s = MagicMock(spec=HistoryStore)
    s.recent.return_value = []
    return s


@pytest.fixture
def runner(config, store):
    return AlertCorrelationRunner(config, store, limit=10)


def test_run_returns_list(runner):
    result = runner.run()
    assert isinstance(result, list)


def test_run_empty_when_no_failures(runner, store):
    store.recent.return_value = []
    events = runner.run()
    assert events == []


def test_run_groups_failures_by_prefix(runner, store):
    def _recent(job_name, limit):
        if job_name in ("backup_daily", "backup_weekly"):
            return [_make_entry(job_name, succeeded=False)]
        return []

    store.recent.side_effect = _recent
    events = runner.run()
    assert len(events) == 1
    assert events[0].correlation_id == "backup"
    assert events[0].size == 2


def test_run_ignores_successful_entries(runner, store):
    store.recent.return_value = [_make_entry("backup_daily", succeeded=True)]
    events = runner.run()
    assert events == []


def test_correlated_property_filters_single_job(runner, store):
    store.recent.side_effect = lambda name, limit: [
        _make_entry(name, succeeded=False)
    ]
    runner.run()
    # Each job has a different prefix (backup_daily -> backup, backup_weekly -> backup, report_daily -> report)
    # backup group has 2 distinct jobs; report group has 1
    correlated = runner.correlated
    assert all(len(set(e.job_names)) > 1 for e in correlated)


def test_summary_lines_returns_strings(runner, store):
    store.recent.return_value = [_make_entry("backup_daily", succeeded=False)]
    runner.run()
    lines = runner.summary_lines()
    assert all(isinstance(l, str) for l in lines)


def test_events_property_returns_copy(runner, store):
    store.recent.return_value = []
    runner.run()
    e1 = runner.events
    e2 = runner.events
    assert e1 is not e2
