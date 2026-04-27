"""Tests for alert_enricher_runner.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alert_enricher import AlertEnricher, EnrichedEntry
from cronwatch.alert_enricher_runner import AlertEnricherRunner
from cronwatch.history import HistoryEntry


def _make_enriched(job: str, consecutive: int) -> EnrichedEntry:
    entry = MagicMock(spec=HistoryEntry)
    entry.job_name = job
    entry.exit_code = 1 if consecutive > 0 else 0
    return EnrichedEntry(
        entry=entry,
        consecutive_failures=consecutive,
    )


@pytest.fixture()
def enricher():
    return MagicMock(spec=AlertEnricher)


@pytest.fixture()
def runner(enricher):
    return AlertEnricherRunner(enricher, min_consecutive_failures=1)


def test_run_returns_self(runner, enricher):
    enricher.enrich_all.return_value = []
    result = runner.run([])
    assert result is runner


def test_results_empty_when_no_entries(runner, enricher):
    enricher.enrich_all.return_value = []
    runner.run([])
    assert runner.results == []


def test_results_filtered_by_min_consecutive(runner, enricher):
    enricher.enrich_all.return_value = [
        _make_enriched("job_a", 2),
        _make_enriched("job_b", 0),
    ]
    runner.run([MagicMock(), MagicMock()])
    assert len(runner.results) == 1
    assert runner.results[0].job_name == "job_a"


def test_min_consecutive_zero_passes_all(enricher):
    r = AlertEnricherRunner(enricher, min_consecutive_failures=0)
    enricher.enrich_all.return_value = [
        _make_enriched("job_a", 0),
        _make_enriched("job_b", 3),
    ]
    r.run([])
    assert len(r.results) == 2


def test_send_called_for_each_result(runner, enricher):
    enriched = [_make_enriched("job_a", 1), _make_enriched("job_b", 2)]
    enricher.enrich_all.return_value = enriched
    send = MagicMock(return_value=True)
    runner.run([], send=send)
    assert send.call_count == 2


def test_send_not_called_when_none(runner, enricher):
    enricher.enrich_all.return_value = [_make_enriched("job_a", 1)]
    # should not raise
    runner.run([], send=None)
    assert len(runner.results) == 1


def test_actionable_returns_non_zero_consecutive(enricher):
    r = AlertEnricherRunner(enricher, min_consecutive_failures=0)
    enricher.enrich_all.return_value = [
        _make_enriched("job_ok", 0),
        _make_enriched("job_bad", 1),
    ]
    r.run([])
    assert len(r.actionable) == 1
    assert r.actionable[0].job_name == "job_bad"
