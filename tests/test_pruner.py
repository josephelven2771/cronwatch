"""Tests for cronwatch.pruner."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import pytest

from cronwatch.history import HistoryStore, HistoryEntry
from cronwatch.pruner import prune_by_age, prune_by_count, prune_all


@pytest.fixture()
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(tmp_path / "history.json")


def _add_entry(store: HistoryStore, job: str, days_ago: float, exit_code: int = 0) -> None:
    started = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    finished = started + timedelta(seconds=10)
    entry = HistoryEntry(
        job_name=job,
        started_at=started,
        finished_at=finished,
        exit_code=exit_code,
    )
    store.record(entry)


def test_prune_by_age_removes_old_entries(store):
    _add_entry(store, "backup", days_ago=10)
    _add_entry(store, "backup", days_ago=3)
    _add_entry(store, "backup", days_ago=1)
    removed = prune_by_age(store, "backup", max_age_days=5)
    assert removed == 1
    assert len(store.all("backup")) == 2


def test_prune_by_age_keeps_all_when_recent(store):
    _add_entry(store, "backup", days_ago=1)
    _add_entry(store, "backup", days_ago=2)
    removed = prune_by_age(store, "backup", max_age_days=30)
    assert removed == 0
    assert len(store.all("backup")) == 2


def test_prune_by_count_removes_oldest(store):
    for i in range(5):
        _add_entry(store, "sync", days_ago=5 - i)
    removed = prune_by_count(store, "sync", max_entries=3)
    assert removed == 2
    assert len(store.all("sync")) == 3


def test_prune_by_count_noop_when_under_limit(store):
    _add_entry(store, "sync", days_ago=1)
    removed = prune_by_count(store, "sync", max_entries=10)
    assert removed == 0


def test_prune_all_applies_to_every_job(store):
    for i in range(4):
        _add_entry(store, "jobA", days_ago=i)
    for i in range(4):
        _add_entry(store, "jobB", days_ago=i)
    results = prune_all(store, max_entries=2)
    assert results["jobA"] == 2
    assert results["jobB"] == 2


def test_prune_all_combined(store):
    _add_entry(store, "jobC", days_ago=20)
    _add_entry(store, "jobC", days_ago=1)
    _add_entry(store, "jobC", days_ago=0.5)
    results = prune_all(store, max_age_days=7, max_entries=1)
    # age prune removes 1 (20 days old), count prune removes 1 more
    assert results["jobC"] == 2
    assert len(store.all("jobC")) == 1
