"""Tests for cronwatch.tracker."""

import time
import pytest
from unittest.mock import MagicMock
from cronwatch.tracker import JobTracker, JobRun
from cronwatch.config import JobConfig


@pytest.fixture
def tracker():
    return JobTracker()


@pytest.fixture
def job_config():
    return JobConfig(name="backup", schedule="0 2 * * *", max_interval_seconds=90000)


def test_record_start_returns_job_run(tracker):
    run = tracker.record_start("backup")
    assert isinstance(run, JobRun)
    assert run.job_name == "backup"
    assert run.started_at > 0
    assert run.finished_at is None


def test_record_finish_sets_fields(tracker):
    run = tracker.record_start("backup")
    tracker.record_finish(run, exit_code=0, output="done")
    assert run.exit_code == 0
    assert run.finished_at is not None
    assert run.output == "done"
    assert run.succeeded is True
    assert run.failed is False


def test_failed_run(tracker):
    run = tracker.record_start("backup")
    tracker.record_finish(run, exit_code=1)
    assert run.failed is True
    assert run.succeeded is False


def test_last_run_none_when_no_runs(tracker, job_config):
    assert tracker.last_run("backup") is None


def test_last_run_returns_most_recent(tracker):
    tracker.record_start("backup")
    run2 = tracker.record_start("backup")
    assert tracker.last_run("backup") is run2


def test_is_overdue_true_when_no_runs(tracker, job_config):
    assert tracker.is_overdue(job_config) is True


def test_is_overdue_false_when_recent_run(tracker, job_config):
    run = tracker.record_start("backup")
    tracker.record_finish(run, exit_code=0)
    assert tracker.is_overdue(job_config) is False


def test_is_overdue_true_when_stale(tracker):
    job = JobConfig(name="backup", schedule="* * * * *", max_interval_seconds=1)
    run = tracker.record_start("backup")
    run.started_at -= 5  # simulate old run
    assert tracker.is_overdue(job) is True


def test_duration(tracker):
    run = tracker.record_start("backup")
    time.sleep(0.05)
    tracker.record_finish(run, exit_code=0)
    assert run.duration is not None
    assert run.duration >= 0.05
