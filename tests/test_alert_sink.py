"""Tests for cronwatch.alert_sink."""
from __future__ import annotations

import datetime
from typing import List

import pytest

from cronwatch.alert_sink import AlertSink, SinkResult
from cronwatch.history import HistoryEntry


def _utc(offset: int = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset)


def _entry(name: str = "backup", success: bool = True) -> HistoryEntry:
    return HistoryEntry(
        job_name=name,
        started_at=_utc(),
        finished_at=_utc(30),
        exit_code=0 if success else 1,
        succeeded=success,
    )


@pytest.fixture()
def sink() -> AlertSink:
    return AlertSink(max_size=10)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_invalid_max_size_raises():
    with pytest.raises(ValueError):
        AlertSink(max_size=0)


def test_initial_size_is_zero(sink):
    assert sink.size == 0


# ---------------------------------------------------------------------------
# Buffering
# ---------------------------------------------------------------------------

def test_add_increments_size(sink):
    sink.add(_entry())
    assert sink.size == 1


def test_peek_returns_copy(sink):
    e = _entry()
    sink.add(e)
    peeked = sink.peek()
    assert peeked == [e]
    # Mutating the returned list does not affect the buffer
    peeked.clear()
    assert sink.size == 1


def test_add_drops_oldest_when_at_capacity():
    s = AlertSink(max_size=3)
    entries = [_entry(name=f"job{i}") for i in range(4)]
    for e in entries:
        s.add(e)
    assert s.size == 3
    assert s.peek()[0].job_name == "job1"  # oldest dropped


# ---------------------------------------------------------------------------
# Flushing
# ---------------------------------------------------------------------------

def test_flush_empty_returns_zero_counts(sink):
    result = sink.flush()
    assert result.flushed == 0
    assert result.targets_notified == 0
    assert bool(result) is True


def test_flush_calls_each_target(sink):
    received: List[List] = []

    def target_a(entries):
        received.append(("a", entries))

    def target_b(entries):
        received.append(("b", entries))

    sink.register(target_a).register(target_b)
    sink.add(_entry())
    result = sink.flush()

    assert result.flushed == 1
    assert result.targets_notified == 2
    assert len(received) == 2


def test_flush_clears_buffer(sink):
    sink.add(_entry())
    sink.flush()
    assert sink.size == 0


def test_flush_records_errors_from_failing_target(sink):
    def bad_target(entries):
        raise RuntimeError("network down")

    sink.register(bad_target)
    sink.add(_entry())
    result = sink.flush()

    assert result.flushed == 1
    assert len(result.errors) == 1
    assert bool(result) is False


# ---------------------------------------------------------------------------
# Draining
# ---------------------------------------------------------------------------

def test_drain_all_clears_buffer(sink):
    sink.add(_entry())
    sink.add(_entry(name="other"))
    drained = sink.drain()
    assert len(drained) == 2
    assert sink.size == 0


def test_drain_with_limit_leaves_remainder(sink):
    for i in range(5):
        sink.add(_entry(name=f"job{i}"))
    drained = sink.drain(limit=2)
    assert len(drained) == 2
    assert sink.size == 3
