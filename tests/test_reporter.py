"""Tests for cronwatch.reporter."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.reporter import Reporter, JobStatus
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import HistoryEntry


@pytest.fixture
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", expected_interval_seconds=86400)


@pytest.fixture
def config(job_config):
    return CronwatchConfig(
        jobs=[job_config],
        alerts=AlertConfig(webhook_url=None, email=None, cooldown_seconds=300),
    )


@pytest.fixture
def store():
    return MagicMock()


@pytest.fixture
def reporter(config, store):
    return Reporter(config, store)


def _entry(minutes_ago: int, exit_code: int = 0, duration: float = 5.0) -> HistoryEntry:
    started = datetime.now(tz=timezone.utc) - timedelta(minutes=minutes_ago)
    return HistoryEntry(
        job_name="backup",
        started_at=started,
        exit_code=exit_code,
        duration_seconds=duration,
    )


def test_collect_healthy(reporter, store):
    store.last.return_value = _entry(minutes_ago=60)
    statuses = reporter.collect()
    assert len(statuses) == 1
    assert statuses[0].healthy is True
    assert statuses[0].missed is False


def test_collect_missed_no_history(reporter, store):
    store.last.return_value = None
    statuses = reporter.collect()
    assert statuses[0].missed is True
    assert statuses[0].healthy is False


def test_collect_missed_stale(reporter, store):
    # interval is 86400s; 1.5x = 36h; entry is 40h old => missed
    store.last.return_value = _entry(minutes_ago=40 * 60)
    statuses = reporter.collect()
    assert statuses[0].missed is True


def test_collect_failed_exit_code(reporter, store):
    store.last.return_value = _entry(minutes_ago=30, exit_code=1)
    statuses = reporter.collect()
    assert statuses[0].healthy is False
    assert statuses[0].missed is False


def test_render_text_contains_job_name(reporter, store):
    store.last.return_value = _entry(minutes_ago=30)
    text = reporter.render_text()
    assert "backup" in text
    assert "OK" in text


def test_render_text_summary_line(reporter, store):
    store.last.return_value = None
    text = reporter.render_text()
    assert "0/1 jobs healthy" in text
    assert "MISSED" in text
