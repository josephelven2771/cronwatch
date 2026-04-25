"""Correlate related alerts into a single correlated event."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.history import HistoryEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CorrelatedEvent:
    """A group of alerts that share a common root cause or pattern."""

    correlation_id: str
    job_names: List[str]
    entries: List[HistoryEntry]
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)

    @property
    def failure_count(self) -> int:
        return sum(1 for e in self.entries if not e.succeeded)

    @property
    def summary(self) -> str:
        jobs = ", ".join(sorted(set(self.job_names)))
        return (
            f"[{self.correlation_id}] {self.size} events across [{jobs}] "
            f"({self.failure_count} failures)"
        )

    def __bool__(self) -> bool:
        return self.size > 0


class AlertCorrelator:
    """Groups HistoryEntry alerts by shared tags or job name prefix."""

    def __init__(self, group_by_prefix: bool = True) -> None:
        self._group_by_prefix = group_by_prefix
        self._buckets: dict[str, List[HistoryEntry]] = {}

    def _correlation_key(self, entry: HistoryEntry) -> str:
        if self._group_by_prefix and "_" in entry.job_name:
            return entry.job_name.rsplit("_", 1)[0]
        return entry.job_name

    def add(self, entry: HistoryEntry) -> str:
        key = self._correlation_key(entry)
        self._buckets.setdefault(key, []).append(entry)
        return key

    def events(self) -> List[CorrelatedEvent]:
        result = []
        for key, entries in self._buckets.items():
            timestamps = [e.started_at for e in entries if e.started_at]
            first = min(timestamps) if timestamps else _utcnow()
            last = max(timestamps) if timestamps else _utcnow()
            tags: List[str] = []
            for e in entries:
                tags.extend(getattr(e, "tags", []) or [])
            result.append(
                CorrelatedEvent(
                    correlation_id=key,
                    job_names=[e.job_name for e in entries],
                    entries=entries,
                    first_seen=first,
                    last_seen=last,
                    tags=list(set(tags)),
                )
            )
        return result

    def clear(self) -> None:
        self._buckets.clear()
