"""Tests for cronwatch.formatter."""
from datetime import datetime, timezone

import pytest

from cronwatch.history import HistoryEntry
from cronwatch.formatter import format_entry, format_entries, format_failure_summary


def _entry(name="backup", succeeded=True, duration=90.0, exit_code=0) -> HistoryEntry:
    e = HistoryEntry.__new__(HistoryEntry)
    e.job_name = name
    e.succeeded = succeeded
    e.started_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    e.finished_at = datetime(2024, 6, 1, 12, 1, 30, tzinfo=timezone.utc)
    e.duration_seconds = duration
    e.exit_code = exit_code
    return e


def test_format_entry_success():
    line = format_entry(_entry())
    assert "[✓]" in line
    assert "backup" in line
    assert "1m 30s" in line
    assert "exit=0" in line


def test_format_entry_failure():
    line = format_entry(_entry(succeeded=False, exit_code=1))
    assert "[✗]" in line
    assert "exit=1" in line


def test_format_entry_short_duration():
    line = format_entry(_entry(duration=45.5))
    assert "45.5s" in line


def test_format_entry_no_exit_code():
    line = format_entry(_entry(exit_code=None))
    assert "no exit code" in line


def test_format_entries_empty():
    out = format_entries([])
    assert "no entries" in out
    assert "Job History" in out


def test_format_entries_with_title():
    entries = [_entry(), _entry(name="cleanup", succeeded=False, exit_code=2)]
    out = format_entries(entries, title="My Jobs")
    assert "My Jobs" in out
    assert "backup" in out
    assert "cleanup" in out


def test_format_failure_summary_no_failures():
    entries = [_entry(), _entry(name="sync")]
    out = format_failure_summary(entries)
    assert out == "No failures recorded."


def test_format_failure_summary_with_failures():
    entries = [
        _entry(),
        _entry(name="deploy", succeeded=False, exit_code=127),
    ]
    out = format_failure_summary(entries)
    assert "1 failure" in out
    assert "deploy" in out
    assert "[✗]" in out
