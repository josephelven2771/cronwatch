"""High-level helper that wires Baseline + AnomalyDetection together."""
from __future__ import annotations

from typing import List, Optional

from cronwatch.anomaly import AnomalyResult, detect_duration_anomaly
from cronwatch.baseline import Baseline
from cronwatch.history import HistoryStore
from cronwatch.config import CronwatchConfig


class AnomalyChecker:
    """Check recent job history for duration anomalies against stored baselines."""

    def __init__(
        self,
        config: CronwatchConfig,
        store: HistoryStore,
        baseline: Baseline,
        z_threshold: float = 3.0,
    ) -> None:
        self._config = config
        self._store = store
        self._baseline = baseline
        self._z_threshold = z_threshold

    def check_job(self, job_name: str) -> Optional[AnomalyResult]:
        """Return an AnomalyResult for the most recent run of *job_name*, or None."""
        entry = self._store.last(job_name)
        if entry is None or entry.duration is None:
            return None
        stats = self._baseline.stats_for(job_name)
        return detect_duration_anomaly(
            job_name=job_name,
            actual_duration=entry.duration,
            stats=stats,
            z_threshold=self._z_threshold,
        )

    def check_all(self) -> List[AnomalyResult]:
        """Return anomaly results for every configured job that has recent history."""
        results: List[AnomalyResult] = []
        for job in self._config.jobs:
            result = self.check_job(job.name)
            if result is not None:
                results.append(result)
        return results

    def anomalies(self) -> List[AnomalyResult]:
        """Return only the anomalous results from check_all."""
        return [r for r in self.check_all() if r.is_anomaly]
