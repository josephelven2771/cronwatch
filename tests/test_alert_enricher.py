"""Tests for alert_enricher.py"""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from cronwatch.alert_enricher import AlertEnricher, EnrichedEntry
from cronwatch.history import HistoryEntry


def _utc(offset_seconds: float = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 10, 12, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset_seconds)


def _entry(job: str, exit_code: int, offset: float = 0) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.job_name = job
    e.exit_code = exit_code
    e.started_at = _utc(offset)
    e.to_dict.return_value = {"job_name": job, "exit_code": exit_code}
    return e


@pytest.fixture()
def store():
    return MagicMock()


@pytest.fixture()
def baseline_store():
    return MagicMock()


@pytest.fixture()
def enricher(store, baseline_store):
    return AlertEnricher(store, baseline_store)


def test_enrich_consecutive_failures_all_failing(enricher, store, baseline_store):
    store.all.return_value = [
        _entry("job_a", 1, 0),
        _entry("job_a", 1, 10),
        _entry("job_a", 1, 20),
    ]
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_a", 1, 30))
    assert result.consecutive_failures == 3


def test_enrich_consecutive_failures_resets_on_success(enricher, store, baseline_store):
    store.all.return_value = [
        _entry("job_a", 0, 0),
        _entry("job_a", 1, 10),
        _entry("job_a", 1, 20),
    ]
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_a", 1, 30))
    assert result.consecutive_failures == 2


def test_enrich_last_success_populated(enricher, store, baseline_store):
    store.all.return_value = [
        _entry("job_b", 0, 0),
        _entry("job_b", 1, 10),
    ]
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_b", 1, 20))
    assert result.last_success_iso is not None


def test_enrich_last_success_none_when_no_success(enricher, store, baseline_store):
    store.all.return_value = [_entry("job_c", 1, 0)]
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_c", 1, 10))
    assert result.last_success_iso is None


def test_enrich_avg_duration_from_baseline(enricher, store, baseline_store):
    store.all.return_value = []
    stats = MagicMock()
    stats.avg_duration = 42.5
    baseline_store.stats_for.return_value = stats
    result = enricher.enrich(_entry("job_d", 0))
    assert result.avg_duration == pytest.approx(42.5)


def test_enrich_avg_duration_none_when_no_baseline(enricher, store, baseline_store):
    store.all.return_value = []
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_e", 0))
    assert result.avg_duration is None


def test_to_dict_contains_enrichment_key(enricher, store, baseline_store):
    store.all.return_value = []
    baseline_store.stats_for.return_value = None
    result = enricher.enrich(_entry("job_f", 1))
    d = result.to_dict()
    assert "enrichment" in d
    assert "consecutive_failures" in d["enrichment"]


def test_enrich_all_returns_list(enricher, store, baseline_store):
    store.all.return_value = []
    baseline_store.stats_for.return_value = None
    entries = [_entry("j", 1), _entry("j", 0)]
    results = enricher.enrich_all(entries)
    assert len(results) == 2
    assert all(isinstance(r, EnrichedEntry) for r in results)
