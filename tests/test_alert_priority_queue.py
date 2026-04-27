"""Tests for cronwatch.alert_priority_queue."""
from __future__ import annotations

import datetime
from typing import Optional

import pytest

from cronwatch.alert_classifier import Severity
from cronwatch.alert_priority_queue import AlertPriorityQueue, DequeuedAlert
from cronwatch.history import HistoryEntry


def _utc(offset: int = 0) -> datetime.datetime:
    return datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset)


def _entry(name: str = "job", succeeded: bool = True) -> HistoryEntry:
    return HistoryEntry(
        job_name=name,
        started_at=_utc(),
        finished_at=_utc(30),
        exit_code=0 if succeeded else 1,
        succeeded=succeeded,
    )


@pytest.fixture()
def queue() -> AlertPriorityQueue:
    return AlertPriorityQueue()


# ---------------------------------------------------------------------------
# Basic enqueue / dequeue
# ---------------------------------------------------------------------------

def test_dequeue_empty_returns_none(queue: AlertPriorityQueue) -> None:
    assert queue.dequeue() is None


def test_size_increments_on_enqueue(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry(), Severity.LOW)
    assert queue.size == 1
    queue.enqueue(_entry(), Severity.MEDIUM)
    assert queue.size == 2


def test_bool_false_when_empty(queue: AlertPriorityQueue) -> None:
    assert not queue


def test_bool_true_when_not_empty(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry(), Severity.LOW)
    assert queue


def test_dequeue_returns_dequeued_alert(queue: AlertPriorityQueue) -> None:
    e = _entry("backup")
    queue.enqueue(e, Severity.HIGH)
    result = queue.dequeue()
    assert isinstance(result, DequeuedAlert)
    assert result.entry is e
    assert result.severity is Severity.HIGH


def test_dequeue_decrements_size(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry(), Severity.MEDIUM)
    queue.dequeue()
    assert queue.size == 0


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

def test_critical_before_low(queue: AlertPriorityQueue) -> None:
    low_entry = _entry("low_job")
    crit_entry = _entry("crit_job", succeeded=False)
    queue.enqueue(low_entry, Severity.LOW)
    queue.enqueue(crit_entry, Severity.CRITICAL)
    first = queue.dequeue()
    assert first is not None
    assert first.severity is Severity.CRITICAL


def test_high_before_medium_before_low(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry("a"), Severity.LOW)
    queue.enqueue(_entry("b"), Severity.HIGH)
    queue.enqueue(_entry("c"), Severity.MEDIUM)
    order = [queue.dequeue().severity for _ in range(3)]  # type: ignore[union-attr]
    assert order == [Severity.HIGH, Severity.MEDIUM, Severity.LOW]


def test_same_severity_fifo(queue: AlertPriorityQueue) -> None:
    """Alerts at equal severity should be dequeued in insertion order."""
    e1 = _entry("first")
    e2 = _entry("second")
    queue.enqueue(e1, Severity.MEDIUM)
    queue.enqueue(e2, Severity.MEDIUM)
    first = queue.dequeue()
    second = queue.dequeue()
    assert first is not None and second is not None
    assert first.entry is e1
    assert second.entry is e2


# ---------------------------------------------------------------------------
# drain
# ---------------------------------------------------------------------------

def test_drain_empties_queue(queue: AlertPriorityQueue) -> None:
    for sev in (Severity.LOW, Severity.HIGH, Severity.CRITICAL, Severity.MEDIUM):
        queue.enqueue(_entry(), sev)
    results = list(queue.drain())
    assert len(results) == 4
    assert queue.size == 0


def test_drain_order_is_priority_order(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry(), Severity.LOW)
    queue.enqueue(_entry(), Severity.CRITICAL)
    queue.enqueue(_entry(), Severity.MEDIUM)
    severities = [r.severity for r in queue.drain()]
    assert severities == [Severity.CRITICAL, Severity.MEDIUM, Severity.LOW]


def test_waited_seconds_non_negative(queue: AlertPriorityQueue) -> None:
    queue.enqueue(_entry(), Severity.HIGH)
    result = queue.dequeue()
    assert result is not None
    assert result.waited_seconds >= 0.0
