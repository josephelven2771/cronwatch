"""alert_batcher.py – collect alerts over a time window and flush them as a batch."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.history import HistoryEntry


@dataclass
class AlertBatch:
    """A group of entries collected during a single flush window."""

    entries: List[HistoryEntry] = field(default_factory=list)
    flushed_at: Optional[float] = None

    @property
    def size(self) -> int:
        return len(self.entries)

    @property
    def failure_count(self) -> int:
        return sum(1 for e in self.entries if not e.succeeded)

    def summary(self) -> str:
        total = self.size
        failures = self.failure_count
        return (
            f"{total} job run(s) in batch; "
            f"{failures} failure(s), {total - failures} success(es)."
        )


FlushCallback = Callable[[AlertBatch], None]


class AlertBatcher:
    """Accumulate HistoryEntry objects and flush them after *window_seconds*.

    Args:
        window_seconds: How long (in seconds) to buffer entries before flushing.
        on_flush: Callable invoked with the completed :class:`AlertBatch`.
        _clock: Injectable clock for testing (defaults to :func:`time.monotonic`).
    """

    def __init__(
        self,
        window_seconds: float,
        on_flush: FlushCallback,
        *,
        _clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._window = window_seconds
        self._on_flush = on_flush
        self._clock = _clock
        self._batch: AlertBatch = AlertBatch()
        self._window_start: float = self._clock()

    def add(self, entry: HistoryEntry) -> None:
        """Add *entry* to the current batch, flushing first if the window expired."""
        if self._is_expired():
            self.flush()
        self._batch.entries.append(entry)

    def flush(self) -> AlertBatch:
        """Flush the current batch immediately and reset the window."""
        batch = self._batch
        batch.flushed_at = self._clock()
        if batch.size > 0:
            self._on_flush(batch)
        self._batch = AlertBatch()
        self._window_start = self._clock()
        return batch

    def pending(self) -> int:
        """Number of entries waiting in the current batch."""
        return self._batch.size

    def _is_expired(self) -> bool:
        return (self._clock() - self._window_start) >= self._window
