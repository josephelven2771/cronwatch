"""Tests for cronwatch.window_checker."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from cronwatch.window_checker import WindowChecker, WindowResult, check_window


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 6, 1, hour, minute, 0, tzinfo=timezone.utc)


def _make_job(name="backup", window_start="02:00", window_end="04:00"):
    return SimpleNamespace(
        name=name,
        window_start=window_start,
        window_end=window_end,
    )


class _FakeStore:
    def __init__(self, last_ran_at=None):
        self._entry = SimpleNamespace(started_at=last_ran_at) if last_ran_at else None

    def last(self, name):
        return self._entry


def test_in_window_returns_true():
    job = _make_job()
    store = _FakeStore(last_ran_at=_utc(3, 0))
    result = check_window(job, store, now=_utc(5, 0))
    assert result.in_window is True
    assert "within window" in result.message


def test_before_window_returns_false():
    job = _make_job()
    store = _FakeStore(last_ran_at=_utc(1, 0))
    result = check_window(job, store, now=_utc(5, 0))
    assert result.in_window is False
    assert "outside window" in result.message


def test_after_window_returns_false():
    job = _make_job()
    store = _FakeStore(last_ran_at=_utc(5, 30))
    result = check_window(job, store, now=_utc(6, 0))
    assert result.in_window is False


def test_no_history_returns_false():
    job = _make_job()
    store = _FakeStore(last_ran_at=None)
    result = check_window(job, store, now=_utc(5, 0))
    assert result.in_window is False
    assert result.last_run is None
    assert "no history" in result.message


def test_window_result_bool_mirrors_in_window():
    job = _make_job()
    store = _FakeStore(last_ran_at=_utc(2, 30))
    result = check_window(job, store, now=_utc(5, 0))
    assert bool(result) is True


def test_check_all_skips_jobs_without_window():
    job_with = _make_job("a", "01:00", "03:00")
    job_without = SimpleNamespace(name="b")  # no window attrs
    config = SimpleNamespace(jobs=[job_with, job_without])
    store = _FakeStore(last_ran_at=_utc(2, 0))
    checker = WindowChecker(config=config, store=store)
    results = checker.check_all(now=_utc(5, 0))
    assert len(results) == 1
    assert results[0].job_name == "a"


def test_violations_filters_out_of_window():
    job = _make_job()
    config = SimpleNamespace(jobs=[job])
    store = _FakeStore(last_ran_at=_utc(0, 0))  # before window
    checker = WindowChecker(config=config, store=store)
    checker.check_all(now=_utc(5, 0))
    assert len(checker.violations) == 1


def test_violations_empty_when_all_healthy():
    job = _make_job()
    config = SimpleNamespace(jobs=[job])
    store = _FakeStore(last_ran_at=_utc(3, 0))
    checker = WindowChecker(config=config, store=store)
    checker.check_all(now=_utc(5, 0))
    assert checker.violations == []
