"""Aggregates multiple alerts into a single batched notification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

from cronwatch.history import HistoryEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AggregatedAlert:
    """A batch of related alert entries collected within a time window."""

    job_name: str
    entries: List[HistoryEntry] = field(default_factory=list)
    opened_at: datetime = field(default_factory=_utcnow)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def failure_count(self) -> int:
        return sum(1 for e in self.entries if not e.succeeded)

    def summary(self) -> str:
        return (
            f"{self.job_name}: {self.failure_count}/{self.count} "
            f"failures since {self.opened_at.strftime('%H:%M:%S UTC')}"
        )


class AlertAggregator:
    """Collects entries per job and flushes a single alert when the window closes."""

    def __init__(self, window_seconds: int = 300) -> None:
        self._window = window_seconds
        self._buckets: dict[str, AggregatedAlert] = {}

    def add(self, entry: HistoryEntry) -> None:
        """Add an entry to the aggregation bucket for its job."""
        job = entry.job_name
        now = _utcnow()
        bucket = self._buckets.get(job)
        if bucket is None or (now - bucket.opened_at).total_seconds() >= self._window:
            bucket = AggregatedAlert(job_name=job, opened_at=now)
            self._buckets[job] = bucket
        bucket.entries.append(entry)

    def flush(
        self,
        job_name: str,
        send_fn: Callable[[AggregatedAlert], None],
    ) -> Optional[AggregatedAlert]:
        """Flush the current bucket for *job_name*, calling *send_fn* if non-empty."""
        bucket = self._buckets.pop(job_name, None)
        if bucket and bucket.failure_count > 0:
            send_fn(bucket)
            return bucket
        return None

    def flush_all(
        self,
        send_fn: Callable[[AggregatedAlert], None],
    ) -> List[AggregatedAlert]:
        """Flush every open bucket and return the ones that triggered *send_fn*."""
        jobs = list(self._buckets.keys())
        sent = []
        for job in jobs:
            result = self.flush(job, send_fn)
            if result is not None:
                sent.append(result)
        return sent
