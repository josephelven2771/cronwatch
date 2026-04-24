"""Tests for cronwatch.alert_aggregator."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cronwatch.alert_aggregator import AggregatedAlert, AlertAggregator
from cronwatch.history import HistoryEntry


def _utc(**kw) -> datetime:
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc) + timedelta(**kw)


def _entry(job: str, succeeded: bool = False, offset_s: int = 0) -> HistoryEntry:
    started = _utc(seconds=offset_s)
    return HistoryEntry(
        job_name=job,
        started_at=started,
        finished_at=started + timedelta(seconds=10),
        exit_code=0 if succeeded else 1,
        succeeded=succeeded,
    )


@pytest.fixture()
def aggregator() -> AlertAggregator:
    return AlertAggregator(window_seconds=60)


def test_add_creates_bucket(aggregator):
    aggregator.add(_entry("backup", succeeded=False))
    assert "backup" in aggregator._buckets


def test_add_accumulates_entries(aggregator):
    aggregator.add(_entry("backup", succeeded=False))
    aggregator.add(_entry("backup", succeeded=True))
    assert aggregator._buckets["backup"].count == 2


def test_failure_count_only_counts_failures(aggregator):
    aggregator.add(_entry("backup", succeeded=False))
    aggregator.add(_entry("backup", succeeded=True))
    aggregator.add(_entry("backup", succeeded=False))
    assert aggregator._buckets["backup"].failure_count == 2


def test_flush_calls_send_fn_on_failures(aggregator):
    aggregator.add(_entry("backup", succeeded=False))
    send_fn = MagicMock()
    result = aggregator.flush("backup", send_fn)
    send_fn.assert_called_once()
    assert result is not None
    assert result.job_name == "backup"


def test_flush_skips_send_fn_when_no_failures(aggregator):
    aggregator.add(_entry("backup", succeeded=True))
    send_fn = MagicMock()
    result = aggregator.flush("backup", send_fn)
    send_fn.assert_not_called()
    assert result is None


def test_flush_removes_bucket(aggregator):
    aggregator.add(_entry("backup", succeeded=False))
    aggregator.flush("backup", MagicMock())
    assert "backup" not in aggregator._buckets


def test_flush_unknown_job_returns_none(aggregator):
    result = aggregator.flush("nonexistent", MagicMock())
    assert result is None


def test_flush_all_returns_only_failure_buckets(aggregator):
    aggregator.add(_entry("job_a", succeeded=False))
    aggregator.add(_entry("job_b", succeeded=True))
    sent = aggregator.flush_all(MagicMock())
    assert len(sent) == 1
    assert sent[0].job_name == "job_a"


def test_new_window_opens_after_expiry(monkeypatch):
    import cronwatch.alert_aggregator as mod
    calls = [_utc(), _utc(seconds=120)]
    idx = iter(calls)
    monkeypatch.setattr(mod, "_utcnow", lambda: next(idx))
    agg = AlertAggregator(window_seconds=60)
    agg.add(_entry("backup", succeeded=False))
    first_opened = agg._buckets["backup"].opened_at
    agg.add(_entry("backup", succeeded=False))
    second_opened = agg._buckets["backup"].opened_at
    assert second_opened != first_opened


def test_summary_format():
    bucket = AggregatedAlert(job_name="nightly", opened_at=_utc())
    bucket.entries.append(_entry("nightly", succeeded=False))
    bucket.entries.append(_entry("nightly", succeeded=True))
    summary = bucket.summary()
    assert "nightly" in summary
    assert "1/2" in summary
