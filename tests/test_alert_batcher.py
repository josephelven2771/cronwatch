"""Tests for cronwatch.alert_batcher."""
from __future__ import annotations

from typing import List
from unittest.mock import MagicMock

import pytest

from cronwatch.alert_batcher import AlertBatch, AlertBatcher
from cronwatch.history import HistoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(job_name: str = "job", succeeded: bool = True) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.job_name = job_name
    e.succeeded = succeeded
    return e


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def flushed() -> List[AlertBatch]:
    return []


@pytest.fixture()
def clock() -> _FakeClock:
    return _FakeClock()


@pytest.fixture()
def batcher(flushed: List[AlertBatch], clock: _FakeClock) -> AlertBatcher:
    return AlertBatcher(window_seconds=10.0, on_flush=flushed.append, _clock=clock)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_add_increments_pending(batcher: AlertBatcher) -> None:
    batcher.add(_entry())
    assert batcher.pending() == 1


def test_flush_invokes_callback(batcher: AlertBatcher, flushed: List[AlertBatch]) -> None:
    batcher.add(_entry())
    batcher.flush()
    assert len(flushed) == 1


def test_flush_resets_pending(batcher: AlertBatcher) -> None:
    batcher.add(_entry())
    batcher.flush()
    assert batcher.pending() == 0


def test_flush_empty_batch_does_not_invoke_callback(
    batcher: AlertBatcher, flushed: List[AlertBatch]
) -> None:
    batcher.flush()
    assert len(flushed) == 0


def test_window_expiry_triggers_flush_on_add(
    batcher: AlertBatcher, clock: _FakeClock, flushed: List[AlertBatch]
) -> None:
    batcher.add(_entry(job_name="first"))
    clock.advance(15.0)  # past the 10-second window
    batcher.add(_entry(job_name="second"))
    # The first batch should have been flushed automatically
    assert len(flushed) == 1
    assert flushed[0].size == 1
    assert batcher.pending() == 1


def test_batch_failure_count(batcher: AlertBatcher, flushed: List[AlertBatch]) -> None:
    batcher.add(_entry(succeeded=True))
    batcher.add(_entry(succeeded=False))
    batcher.add(_entry(succeeded=False))
    batcher.flush()
    assert flushed[0].failure_count == 2


def test_batch_summary_string(batcher: AlertBatcher, flushed: List[AlertBatch]) -> None:
    batcher.add(_entry(succeeded=True))
    batcher.add(_entry(succeeded=False))
    batcher.flush()
    summary = flushed[0].summary()
    assert "2 job run(s)" in summary
    assert "1 failure" in summary


def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError):
        AlertBatcher(window_seconds=0, on_flush=lambda b: None)


def test_flush_returns_batch(batcher: AlertBatcher) -> None:
    batcher.add(_entry())
    batch = batcher.flush()
    assert isinstance(batch, AlertBatch)
    assert batch.size == 1
