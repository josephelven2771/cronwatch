"""Run alert correlation across all recent history entries."""
from __future__ import annotations

from typing import List, Optional

from cronwatch.alert_correlation import AlertCorrelator, CorrelatedEvent
from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore


class AlertCorrelationRunner:
    """Builds correlated events from a HistoryStore for all configured jobs."""

    def __init__(
        self,
        config: CronwatchConfig,
        store: HistoryStore,
        limit: int = 50,
        group_by_prefix: bool = True,
    ) -> None:
        self._config = config
        self._store = store
        self._limit = limit
        self._correlator = AlertCorrelator(group_by_prefix=group_by_prefix)
        self._events: List[CorrelatedEvent] = []

    def run(self) -> List[CorrelatedEvent]:
        self._correlator.clear()
        for job in self._config.jobs:
            entries = self._store.recent(job.name, self._limit)
            for entry in entries:
                if not entry.succeeded:
                    self._correlator.add(entry)
        self._events = self._correlator.events()
        return self._events

    @property
    def events(self) -> List[CorrelatedEvent]:
        return list(self._events)

    @property
    def correlated(self) -> List[CorrelatedEvent]:
        """Return only events with more than one distinct job involved."""
        return [
            e for e in self._events if len(set(e.job_names)) > 1
        ]

    def summary_lines(self) -> List[str]:
        return [e.summary for e in self._events]
