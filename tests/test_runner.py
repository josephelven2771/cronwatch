"""Tests for cronwatch.runner."""
from __future__ import annotations

import pytest

from cronwatch.config import JobConfig
from cronwatch.history import HistoryStore
from cronwatch.runner import RunResult, run_job


@pytest.fixture()
def store(tmp_path):
    return HistoryStore(path=str(tmp_path / "history.json"))


@pytest.fixture()
def job():
    return JobConfig(name="test-job", command="echo hello", schedule="* * * * *")


def test_run_job_success(store, job):
    result = run_job(job, store)
    assert isinstance(result, RunResult)
    assert result.succeeded
    assert result.exit_code == 0
    assert result.job_name == "test-job"


def test_run_job_records_to_store(store, job):
    run_job(job, store)
    entry = store.last("test-job")
    assert entry is not None
    assert entry.succeeded


def test_run_job_failure(store):
    failing = JobConfig(name="fail-job", command="exit 1", schedule="* * * * *")
    result = run_job(failing, store)
    assert not result.succeeded
    assert result.exit_code == 1


def test_run_job_failure_recorded(store):
    failing = JobConfig(name="fail-job", command="exit 2", schedule="* * * * *")
    run_job(failing, store)
    entry = store.last("fail-job")
    assert entry is not None
    assert not entry.succeeded


def test_run_job_timeout(store):
    slow = JobConfig(name="slow-job", command="sleep 10", schedule="* * * * *")
    result = run_job(slow, store, timeout=1)
    assert not result.succeeded
    assert result.exit_code == 124
    assert "Timed out" in result.stderr


def test_run_job_duration_positive(store, job):
    result = run_job(job, store)
    assert result.duration_seconds >= 0


def test_run_result_stdout_captured(store):
    j = JobConfig(name="echo-job", command="echo cronwatch", schedule="* * * * *")
    result = run_job(j, store)
    assert "cronwatch" in result.stdout
