"""High-level checker that evaluates thresholds for all configured jobs."""
from __future__ import annotations

from typing import Dict, List

from cronwatch.baseline import Baseline
from cronwatch.config import CronwatchConfig
from cronwatch.threshold import ThresholdPolicy, ThresholdResult, check_threshold


class ThresholdChecker:
    """Runs threshold checks against baseline data for every configured job."""

    def __init__(
        self,
        config: CronwatchConfig,
        baseline: Baseline,
        policy: ThresholdPolicy | None = None,
    ) -> None:
        self._config = config
        self._baseline = baseline
        self._policy = policy or ThresholdPolicy()
        self._results: Dict[str, ThresholdResult] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_job(self, job_name: str) -> ThresholdResult:
        """Check a single job and cache the result."""
        stats = self._baseline.stats_for(job_name)
        result = check_threshold(job_name, stats, self._policy)
        self._results[job_name] = result
        return result

    def check_all(self) -> List[ThresholdResult]:
        """Check every job defined in config and return all results."""
        return [self.check_job(j.name) for j in self._config.jobs]

    @property
    def breaches(self) -> List[ThresholdResult]:
        """Return only the results where a threshold was breached."""
        return [r for r in self._results.values() if r.breached]
