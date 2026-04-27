"""Tests for cronwatch.alert_score."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.alert_score import AlertScore, ScoreFactors, score_job, _consec_component
from cronwatch.history import HistoryEntry


def _utc(year: int = 2024, month: int = 1, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _entry(succeeded: bool, job: str = "backup") -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.job_name = job
    e.succeeded = succeeded
    return e


@pytest.fixture()
def store():
    return MagicMock()


@pytest.fixture()
def baseline_store():
    return MagicMock()


# ---------------------------------------------------------------------------
# ScoreFactors / AlertScore unit tests
# ---------------------------------------------------------------------------

def test_alert_score_bool_true_at_threshold():
    s = AlertScore(job_name="x", score=0.5)
    assert bool(s) is True


def test_alert_score_bool_false_below_threshold():
    s = AlertScore(job_name="x", score=0.49)
    assert bool(s) is False


def test_consec_component_caps_at_one():
    assert _consec_component(100) == 1.0


def test_consec_component_zero_for_no_failures():
    assert _consec_component(0) == 0.0


def test_consec_component_partial():
    result = _consec_component(2)   # 2/5 = 0.4
    assert abs(result - 0.4) < 1e-9


# ---------------------------------------------------------------------------
# score_job — no history
# ---------------------------------------------------------------------------

def test_score_job_no_history_returns_zero(store, baseline_store):
    store.get.return_value = []
    baseline_store.stats_for.return_value = None

    result = score_job("backup", store, baseline_store)

    assert result.job_name == "backup"
    assert result.score == 0.0
    assert result.factors.runs_available == 0


def test_score_job_no_history_anomaly_nonzero(store, baseline_store):
    store.get.return_value = []
    baseline_store.stats_for.return_value = None

    result = score_job("backup", store, baseline_store, is_anomalous=True)

    assert result.score > 0.0
    assert result.factors.is_anomalous is True


# ---------------------------------------------------------------------------
# score_job — with history
# ---------------------------------------------------------------------------

def test_score_job_all_success_low_score(store, baseline_store):
    store.get.return_value = [_entry(True)] * 10
    stats = MagicMock()
    stats.consecutive_failures = 0
    baseline_store.stats_for.return_value = stats

    result = score_job("backup", store, baseline_store)

    assert result.score < 0.1
    assert bool(result) is False


def test_score_job_all_failures_high_score(store, baseline_store):
    store.get.return_value = [_entry(False)] * 10
    stats = MagicMock()
    stats.consecutive_failures = 10
    baseline_store.stats_for.return_value = stats

    result = score_job("backup", store, baseline_store)

    assert result.score >= 0.8
    assert bool(result) is True


def test_score_job_mixed_failures(store, baseline_store):
    entries = [_entry(False)] * 4 + [_entry(True)] * 6   # 40 % failure
    store.get.return_value = entries
    stats = MagicMock()
    stats.consecutive_failures = 2
    baseline_store.stats_for.return_value = stats

    result = score_job("backup", store, baseline_store)

    assert 0.1 < result.score < 0.9
    assert result.factors.failure_rate == pytest.approx(0.4)
    assert result.factors.consecutive_failures == 2
    assert result.factors.runs_available == 10


def test_score_capped_at_one(store, baseline_store):
    store.get.return_value = [_entry(False)] * 20
    stats = MagicMock()
    stats.consecutive_failures = 999
    baseline_store.stats_for.return_value = stats

    result = score_job("backup", store, baseline_store, is_anomalous=True)

    assert result.score <= 1.0


def test_score_job_no_baseline_stats_uses_zero_consec(store, baseline_store):
    store.get.return_value = [_entry(False)] * 5 + [_entry(True)] * 5
    baseline_store.stats_for.return_value = None

    result = score_job("backup", store, baseline_store)

    assert result.factors.consecutive_failures == 0
    assert result.score > 0.0
