"""Priority queue for ordering alerts before dispatch.

Alerts are enqueued with a severity level and dequeued in
highest-priority-first order.  Ties are broken by insertion time so
older alerts are dispatched before newer ones of equal severity.
"""
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from cronwatch.alert_classifier import Severity
from cronwatch.history import HistoryEntry

# Lower integer → higher priority (CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3)
_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


@dataclass(order=True)
class _QueueItem:
    priority: int
    inserted_at: float
    entry: HistoryEntry = field(compare=False)
    severity: Severity = field(compare=False)


@dataclass
class DequeuedAlert:
    entry: HistoryEntry
    severity: Severity
    waited_seconds: float

    def __bool__(self) -> bool:  # pragma: no cover
        return True


class AlertPriorityQueue:
    """Thread-unsafe in-memory priority queue for HistoryEntry alerts."""

    def __init__(self) -> None:
        self._heap: List[_QueueItem] = []

    # ------------------------------------------------------------------
    def enqueue(self, entry: HistoryEntry, severity: Severity) -> None:
        """Add *entry* to the queue at the appropriate priority tier."""
        item = _QueueItem(
            priority=_SEVERITY_ORDER[severity],
            inserted_at=time.monotonic(),
            entry=entry,
            severity=severity,
        )
        heapq.heappush(self._heap, item)

    def dequeue(self) -> Optional[DequeuedAlert]:
        """Remove and return the highest-priority alert, or *None* if empty."""
        if not self._heap:
            return None
        item = heapq.heappop(self._heap)
        waited = time.monotonic() - item.inserted_at
        return DequeuedAlert(entry=item.entry, severity=item.severity, waited_seconds=waited)

    def drain(self) -> Iterator[DequeuedAlert]:
        """Yield all alerts in priority order, emptying the queue."""
        while self._heap:
            result = self.dequeue()
            if result is not None:
                yield result

    # ------------------------------------------------------------------
    @property
    def size(self) -> int:
        return len(self._heap)

    def __len__(self) -> int:
        return self.size

    def __bool__(self) -> bool:
        return bool(self._heap)
