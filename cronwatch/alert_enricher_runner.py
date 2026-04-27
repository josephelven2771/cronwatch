"""alert_enricher_runner.py – Pipeline step that enriches and filters alert candidates."""
from __future__ import annotations

from typing import Callable, List, Optional

from cronwatch.alert_enricher import AlertEnricher, EnrichedEntry
from cronwatch.history import HistoryEntry


SendFn = Callable[[EnrichedEntry], bool]


class AlertEnricherRunner:
    """Enrich a batch of entries then optionally dispatch them."""

    def __init__(
        self,
        enricher: AlertEnricher,
        min_consecutive_failures: int = 1,
    ) -> None:
        self._enricher = enricher
        self._min_consecutive = min_consecutive_failures
        self._results: List[EnrichedEntry] = []

    # ------------------------------------------------------------------
    def run(
        self,
        entries: List[HistoryEntry],
        send: Optional[SendFn] = None,
    ) -> "AlertEnricherRunner":
        enriched = self._enricher.enrich_all(entries)
        self._results = [
            e for e in enriched
            if e.consecutive_failures >= self._min_consecutive
        ]
        if send is not None:
            for e in self._results:
                send(e)
        return self

    # ------------------------------------------------------------------
    @property
    def results(self) -> List[EnrichedEntry]:
        return list(self._results)

    @property
    def actionable(self) -> List[EnrichedEntry]:
        """Entries that have at least one consecutive failure."""
        return [e for e in self._results if e.consecutive_failures > 0]
