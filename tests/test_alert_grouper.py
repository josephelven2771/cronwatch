"""Tests for cronwatch.alert_grouper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from cronwatch.alert_grouper import AlertGroup, AlertGrouper, _default_key
from cronwatch.history import HistoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(year: int = 2024, second: int = 0) -> datetime:
    return datetime(year, 1, 1, 0, 0, second, tzinfo=timezone.utc)


def _entry(
    job_name: str = "backup.daily",
    succeeded: bool = True,
    exit_code: int = 0,
) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=_utc(second=0),
        finished_at=_utc(second=5),
        succeeded=succeeded,
        exit_code=exit_code,
        duration=5.0,
    )


# ---------------------------------------------------------------------------
# AlertGroup unit tests
# ---------------------------------------------------------------------------

def test_alert_group_size_and_bool():
    g = AlertGroup(key="backup")
    assert g.size == 0
    assert not g
    g.entries.append(_entry())
    assert g.size == 1
    assert bool(g)


def test_alert_group_failure_count():
    g = AlertGroup(key="backup")
    g.entries.append(_entry(succeeded=True))
    g.entries.append(_entry(succeeded=False, exit_code=1))
    assert g.failure_count == 1


def test_alert_group_summary_all_healthy():
    g = AlertGroup(key="db")
    g.entries.append(_entry(job_name="db.vacuum", succeeded=True))
    assert "all healthy" in g.summary
    assert "[db]" in g.summary


def test_alert_group_summary_with_failures():
    g = AlertGroup(key="db")
    g.entries.append(_entry(job_name="db.vacuum", succeeded=False, exit_code=1))
    assert "1 failure" in g.summary


# ---------------------------------------------------------------------------
# _default_key
# ---------------------------------------------------------------------------

def test_default_key_splits_on_dot():
    e = _entry(job_name="backup.daily")
    assert _default_key(e) == "backup"


def test_default_key_no_dot():
    e = _entry(job_name="cleanup")
    assert _default_key(e) == "cleanup"


# ---------------------------------------------------------------------------
# AlertGrouper
# ---------------------------------------------------------------------------

@pytest.fixture()
def grouper() -> AlertGrouper:
    return AlertGrouper()


def test_add_creates_group(grouper: AlertGrouper):
    grouper.add(_entry(job_name="backup.daily"))
    g = grouper.group("backup")
    assert g is not None
    assert g.size == 1


def test_add_accumulates_into_same_group(grouper: AlertGrouper):
    grouper.add(_entry(job_name="backup.daily"))
    grouper.add(_entry(job_name="backup.weekly"))
    assert grouper.group("backup").size == 2  # type: ignore[union-attr]


def test_all_groups_returns_every_group(grouper: AlertGrouper):
    grouper.add(_entry(job_name="backup.daily"))
    grouper.add(_entry(job_name="report.weekly"))
    keys = {g.key for g in grouper.all_groups()}
    assert keys == {"backup", "report"}


def test_problem_groups_filters_healthy(grouper: AlertGrouper):
    grouper.add(_entry(job_name="backup.daily", succeeded=True))
    grouper.add(_entry(job_name="report.weekly", succeeded=False, exit_code=2))
    problems = grouper.problem_groups()
    assert len(problems) == 1
    assert problems[0].key == "report"


def test_custom_key_fn():
    grouper = AlertGrouper(key_fn=lambda e: e.job_name[-3:])
    grouper.add(_entry(job_name="backup.daily"))
    grouper.add(_entry(job_name="report.daily"))
    # both end in 'ily' -> same group
    assert len(grouper.all_groups()) == 1


def test_clear_removes_all_groups(grouper: AlertGrouper):
    grouper.add(_entry(job_name="backup.daily"))
    grouper.clear()
    assert grouper.all_groups() == []
