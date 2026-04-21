"""High-level checker that runs trend analysis across all configured jobs."""
from __future__ import annotations

from typing import Dict, List, Optional

from cronwatch.baseline import Baseline
from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore
from cronwatch.trend import TrendResult, analyze_trend


class TrendChecker:
    """Runs trend analysis for every job defined in config."""

    def __init__(
        self,
        config: CronwatchConfig,
        store: HistoryStore,
        baseline: Baseline,
        window: int = 20,
        duration_slope_threshold: float = 5.0,
    ) -> None:
        self._config = config
        self._store = store
        self._baseline = baseline
        self._window = window
        self._threshold = duration_slope_threshold
        self._results: Dict[str, TrendResult] = {}

    def check_job(self, job_name: str) -> TrendResult:
        """Analyse trend for a single job and cache the result."""
        entries = self._store.get(job_name, limit=self._window)
        recent_durations: List[float] = [
            e.duration for e in entries if e.duration is not None
        ]

        baseline_stats = self._baseline.stats_for(job_name)

        recent_failure_rate: Optional[float] = None
        if entries:
            failures = sum(1 for e in entries if not e.succeeded)
            recent_failure_rate = failures / len(entries)

        result = analyze_trend(
            job_name=job_name,
            recent_durations=recent_durations,
            baseline=baseline_stats,
            recent_failure_rate=recent_failure_rate,
            duration_slope_threshold=self._threshold,
        )
        self._results[job_name] = result
        return result

    def check_all(self) -> List[TrendResult]:
        """Run trend analysis for all jobs in config."""
        results = []
        for job in self._config.jobs:
            results.append(self.check_job(job.name))
        return results

    @property
    def degrading(self) -> List[TrendResult]:
        """Return only results flagged as degrading."""
        return [r for r in self._results.values() if r.direction == "degrading"]
