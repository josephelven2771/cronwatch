"""Tests for cronwatch.filter."""
from datetime import datetime, timedelta

import pytest

from cronwatch.filter import (
    FilterCriteria,
    filter_entries,
    filter_by_job,
    filter_failures,
)
from cronwatch.history import HistoryEntry


def _entry(job_name: str, offset_minutes: int = 0, succeeded: bool = True) -> HistoryEntry:
    start = datetime(2024, 1, 1, 12, 0) + timedelta(minutes=offset_minutes)
    end = start + timedelta(seconds=30)
    return HistoryEntry(
        job_name=job_name,
        started_at=start,
        finished_at=end,
        exit_code=0 if succeeded else 1,
        succeeded=succeeded,
        output="ok" if succeeded else "err",
    )


ENTRIES = [
    _entry("backup", 0, succeeded=True),
    _entry("backup", 10, succeeded=False),
    _entry("cleanup", 5, succeeded=True),
    _entry("cleanup", 15, succeeded=False),
]


def test_filter_by_job_name():
    result = filter_by_job(ENTRIES, "backup")
    assert all(e.job_name == "backup" for e in result)
    assert len(result) == 2


def test_filter_failures_only():
    result = filter_failures(ENTRIES)
    assert all(not e.succeeded for e in result)
    assert len(result) == 2


def test_filter_succeeded_only():
    result = filter_entries(ENTRIES, FilterCriteria(succeeded_only=True))
    assert all(e.succeeded for e in result)
    assert len(result) == 2


def test_filter_since():
    since = datetime(2024, 1, 1, 12, 8)
    result = filter_entries(ENTRIES, FilterCriteria(since=since))
    assert all(e.started_at >= since for e in result)


def test_filter_until():
    until = datetime(2024, 1, 1, 12, 8)
    result = filter_entries(ENTRIES, FilterCriteria(until=until))
    assert all(e.started_at <= until for e in result)


def test_filter_limit():
    result = filter_entries(ENTRIES, FilterCriteria(limit=2))
    assert len(result) == 2


def test_filter_combined():
    result = filter_entries(
        ENTRIES,
        FilterCriteria(job_name="cleanup", failed_only=True),
    )
    assert len(result) == 1
    assert result[0].job_name == "cleanup"
    assert not result[0].succeeded


def test_results_sorted_chronologically():
    result = filter_entries(ENTRIES, FilterCriteria())
    times = [e.started_at for e in result]
    assert times == sorted(times)
