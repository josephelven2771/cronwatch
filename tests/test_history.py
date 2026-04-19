"""Tests for cronwatch.history module."""

import pytest
from pathlib import Path

from cronwatch.history import HistoryEntry, JobHistory


@pytest.fixture
def history(tmp_path):
    return JobHistory(path=tmp_path / "history.json")


def _entry(job_name="backup", started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:01:00", exit_code=0):
    return HistoryEntry(job_name=job_name, started_at=started_at, finished_at=finished_at, exit_code=exit_code)


def test_record_and_retrieve(history):
    e = _entry()
    history.record(e)
    entries = history.get("backup")
    assert len(entries) == 1
    assert entries[0].job_name == "backup"
    assert entries[0].exit_code == 0


def test_last_returns_most_recent(history):
    history.record(_entry(started_at="2024-01-01T00:00:00"))
    history.record(_entry(started_at="2024-01-02T00:00:00"))
    last = history.last("backup")
    assert last is not None
    assert last.started_at == "2024-01-02T00:00:00"


def test_last_returns_none_for_unknown_job(history):
    assert history.last("nonexistent") is None


def test_succeeded_true_on_exit_zero(history):
    e = _entry(exit_code=0)
    assert e.succeeded is True


def test_succeeded_false_on_nonzero_exit(history):
    e = _entry(exit_code=1)
    assert e.succeeded is False


def test_get_limit(history):
    for i in range(10):
        history.record(_entry(started_at=f"2024-01-{i+1:02d}T00:00:00"))
    entries = history.get("backup", limit=3)
    assert len(entries) == 3
    assert entries[-1].started_at == "2024-01-10T00:00:00"


def test_clear_specific_job(history):
    history.record(_entry(job_name="backup"))
    history.record(_entry(job_name="sync"))
    history.clear("backup")
    assert history.get("backup") == []
    assert len(history.get("sync")) == 1


def test_clear_all(history):
    history.record(_entry(job_name="backup"))
    history.record(_entry(job_name="sync"))
    history.clear()
    assert history.get("backup") == []
    assert history.get("sync") == []


def test_multiple_jobs_isolated(history):
    history.record(_entry(job_name="a"))
    history.record(_entry(job_name="b"))
    assert len(history.get("a")) == 1
    assert len(history.get("b")) == 1
