"""Tests for cronwatch.monitor."""

import pytest
from unittest.mock import patch, MagicMock
from cronwatch.monitor import Monitor
from cronwatch.tracker import JobTracker
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig


@pytest.fixture
def config():
    return CronwatchConfig(
        jobs=[
            JobConfig(name="backup", schedule="0 2 * * *", max_interval_seconds=90000),
        ],
        alerts=AlertConfig(webhook_url="http://example.com/hook"),
    )


@pytest.fixture
def tracker():
    return JobTracker()


@pytest.fixture
def monitor(config, tracker):
    return Monitor(config=config, tracker=tracker)


@patch("cronwatch.monitor.dispatch_alert")
def test_check_all_alerts_on_missed_job(mock_dispatch, monitor):
    alerts = monitor.check_all()
    assert len(alerts) == 1
    assert "MISSED" in alerts[0]
    mock_dispatch.assert_called_once()


@patch("cronwatch.monitor.dispatch_alert")
def test_check_all_no_alert_on_healthy_job(mock_dispatch, monitor, tracker):
    run = tracker.record_start("backup")
    tracker.record_finish(run, exit_code=0)
    alerts = monitor.check_all()
    assert alerts == []
    mock_dispatch.assert_not_called()


@patch("cronwatch.monitor.dispatch_alert")
def test_check_all_alerts_on_failed_job(mock_dispatch, monitor, tracker, config):
    # Make the job appear recent but failed
    config.jobs[0].max_interval_seconds = 99999
    run = tracker.record_start("backup")
    tracker.record_finish(run, exit_code=2, output="error occurred")
    alerts = monitor.check_all()
    assert any("FAILED" in a for a in alerts)
    mock_dispatch.assert_called_once()
