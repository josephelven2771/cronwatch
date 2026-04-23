"""High-level checker that evaluates health for all configured jobs."""
from __future__ import annotations

from typing import Dict, List

from cronwatch.anomaly_checker import AnomalyChecker
from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore
from cronwatch.job_health import JobHealthResult, evaluate_job_health
from cronwatch.threshold_checker import ThresholdChecker
from cronwatch.trend_checker import TrendChecker


class JobHealthChecker:
    """Runs all signal checkers and aggregates results per job."""

    def __init__(
        self,
        config: CronwatchConfig,
        store: HistoryStore,
        *,
        anomaly_checker: AnomalyChecker | None = None,
        threshold_checker: ThresholdChecker | None = None,
        trend_checker: TrendChecker | None = None,
    ) -> None:
        self._config = config
        self._store = store
        self._anomaly = anomaly_checker
        self._threshold = threshold_checker
        self._trend = trend_checker

    # ------------------------------------------------------------------
    def check_all(self) -> Dict[str, JobHealthResult]:
        """Return a mapping of job_name -> JobHealthResult for every job."""
        anomalies = self._anomaly.check_all() if self._anomaly else {}
        thresholds = self._threshold.check_all() if self._threshold else {}
        trends = self._trend.check_all() if self._trend else {}

        results: Dict[str, JobHealthResult] = {}
        for job in self._config.jobs:
            results[job.name] = evaluate_job_health(
                job.name,
                anomaly=anomalies.get(job.name),
                threshold=thresholds.get(job.name),
                trend=trends.get(job.name),
            )
        return results

    def unhealthy(self) -> List[JobHealthResult]:
        """Return only jobs that have at least one failing signal."""
        return [r for r in self.check_all().values() if not r.healthy]
