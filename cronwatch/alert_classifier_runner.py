"""High-level helper that classifies all jobs and returns actionable results."""
from __future__ import annotations

from typing import Dict, List

from cronwatch.alert_classifier import ClassificationResult, Severity, classify
from cronwatch.baseline import BaselineStore
from cronwatch.checkpoint import JobCheckpoint
from cronwatch.checkpoint_manager import CheckpointManager
from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore


class AlertClassifierRunner:
    """Classify all configured jobs and surface HIGH/CRITICAL results."""

    def __init__(
        self,
        config: CronwatchConfig,
        store: HistoryStore,
        baseline: BaselineStore,
        checkpoints: CheckpointManager,
    ) -> None:
        self._config = config
        self._store = store
        self._baseline = baseline
        self._checkpoints = checkpoints
        self._results: Dict[str, ClassificationResult] = {}

    def run(self) -> None:
        """Classify every configured job and cache results."""
        self._results.clear()
        for job in self._config.jobs:
            entry = self._store.last(job.name)
            if entry is None:
                continue
            stats = self._baseline.stats_for(job.name)
            fr = stats.failure_rate if stats else None
            cf = self._checkpoints.consecutive_failures(job.name)
            result = classify(job.name, entry, consecutive_failures=cf, failure_rate=fr)
            self._results[job.name] = result

    @property
    def results(self) -> Dict[str, ClassificationResult]:
        """All classification results keyed by job name."""
        return dict(self._results)

    def actionable(self) -> List[ClassificationResult]:
        """Return only HIGH or CRITICAL results."""
        return [r for r in self._results.values() if bool(r)]

    def by_severity(self, severity: Severity) -> List[ClassificationResult]:
        """Filter results to a specific severity level."""
        return [r for r in self._results.values() if r.severity == severity]
