"""alert_enricher.py – Attach contextual metadata to alert entries before dispatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from cronwatch.history import HistoryStore
from cronwatch.baseline import BaselineStore
from cronwatch.history import HistoryEntry


@dataclass
class EnrichedEntry:
    """An alert entry decorated with extra context."""

    entry: HistoryEntry
    consecutive_failures: int = 0
    avg_duration: Optional[float] = None
    last_success_iso: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def job_name(self) -> str:  # convenience pass-through
        return self.entry.job_name

    def to_dict(self) -> Dict[str, Any]:
        base = self.entry.to_dict()
        base["enrichment"] = {
            "consecutive_failures": self.consecutive_failures,
            "avg_duration": self.avg_duration,
            "last_success_iso": self.last_success_iso,
            **self.extra,
        }
        return base


class AlertEnricher:
    """Enriches a HistoryEntry with baseline and history context."""

    def __init__(self, store: HistoryStore, baseline_store: BaselineStore) -> None:
        self._store = store
        self._baseline = baseline_store

    def enrich(self, entry: HistoryEntry) -> EnrichedEntry:
        name = entry.job_name
        history = self._store.all(name)

        consecutive = 0
        for past in reversed(history):
            if past.exit_code != 0:
                consecutive += 1
            else:
                break

        last_success: Optional[str] = None
        for past in reversed(history):
            if past.exit_code == 0:
                last_success = past.started_at.isoformat() if past.started_at else None
                break

        stats = self._baseline.stats_for(name)
        avg_dur = stats.avg_duration if stats else None

        return EnrichedEntry(
            entry=entry,
            consecutive_failures=consecutive,
            avg_duration=avg_dur,
            last_success_iso=last_success,
        )

    def enrich_all(self, entries: list[HistoryEntry]) -> list[EnrichedEntry]:
        return [self.enrich(e) for e in entries]
