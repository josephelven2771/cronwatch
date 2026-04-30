"""alert_sink.py — Collects and drains alert entries to one or more output targets.

An AlertSink buffers incoming entries and flushes them to registered
send functions in bulk, optionally enforcing a maximum buffer size.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.history import HistoryEntry


SendFn = Callable[[List[HistoryEntry]], None]


@dataclass
class SinkResult:
    flushed: int
    targets_notified: int
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return len(self.errors) == 0


class AlertSink:
    """Buffer alert entries and flush them to registered send targets."""

    def __init__(self, max_size: int = 500) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._buffer: List[HistoryEntry] = []
        self._targets: List[SendFn] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, fn: SendFn) -> "AlertSink":
        """Register a send function as a flush target."""
        self._targets.append(fn)
        return self

    # ------------------------------------------------------------------
    # Buffering
    # ------------------------------------------------------------------

    def add(self, entry: HistoryEntry) -> None:
        """Add an entry to the buffer, dropping oldest if at capacity."""
        if len(self._buffer) >= self._max_size:
            self._buffer.pop(0)
        self._buffer.append(entry)

    @property
    def size(self) -> int:
        """Number of entries currently buffered."""
        return len(self._buffer)

    def peek(self) -> List[HistoryEntry]:
        """Return a copy of the current buffer without flushing."""
        return list(self._buffer)

    # ------------------------------------------------------------------
    # Flushing
    # ------------------------------------------------------------------

    def flush(self) -> SinkResult:
        """Send all buffered entries to every registered target and clear buffer."""
        if not self._buffer:
            return SinkResult(flushed=0, targets_notified=0)

        entries = list(self._buffer)
        errors: List[str] = []
        notified = 0

        for fn in self._targets:
            try:
                fn(entries)
                notified += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{fn.__name__}: {exc}")

        self._buffer.clear()
        return SinkResult(flushed=len(entries), targets_notified=notified, errors=errors)

    def drain(self, limit: Optional[int] = None) -> List[HistoryEntry]:
        """Remove and return up to *limit* entries without sending them."""
        if limit is None:
            entries, self._buffer = self._buffer, []
        else:
            entries, self._buffer = self._buffer[:limit], self._buffer[limit:]
        return entries
