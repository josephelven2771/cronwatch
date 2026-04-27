"""Alert scoring: compute a numeric urgency score for a job entry.

The score combines failure rate, consecutive failures, anomaly status,
and recency into a single float in [0.0, 1.0] that callers can use to
prioritise or filter alerts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwatch.history import HistoryStore
from cronwatch.baseline import BaselineStore, BaselineStats


@dataclass
class ScoreFactors:
    failure_rate: float = 0.0          # 0..1
    consecutive_failures: int = 0
    is_anomalous: bool = False
    runs_available: int = 0


@dataclass
class AlertScore:
    job_name: str
    score: float                        # 0.0 (healthy) .. 1.0 (critical)
    factors: ScoreFactors = field(default_factory=ScoreFactors)

    def __bool__(self) -> bool:
        """True when the score is above the default actionable threshold."""
        return self.score >= 0.5

    def __repr__(self) -> str:  # pragma: no cover
        return f"AlertScore({self.job_name!r}, score={self.score:.3f})"


# Weights must sum to 1.0
_W_FAILURE_RATE = 0.45
_W_CONSEC = 0.35
_W_ANOMALY = 0.20
_CONSEC_CAP = 5          # consecutive failures at which weight is fully applied


def _consec_component(n: int) -> float:
    return min(n / _CONSEC_CAP, 1.0)


def score_job(
    job_name: str,
    store: HistoryStore,
    baseline_store: BaselineStore,
    *,
    window: int = 20,
    is_anomalous: bool = False,
) -> AlertScore:
    """Return an :class:`AlertScore` for *job_name*.

    Parameters
    ----------
    job_name:
        Name of the cron job to evaluate.
    store:
        History store used to look up recent runs.
    baseline_store:
        Baseline store that holds aggregate stats.
    window:
        Number of recent entries to consider when computing failure rate.
    is_anomalous:
        Whether an anomaly detector has flagged this job's latest run.
    """
    entries = store.get(job_name, limit=window)
    runs = len(entries)

    if runs == 0:
        factors = ScoreFactors(is_anomalous=is_anomalous)
        raw = _W_ANOMALY if is_anomalous else 0.0
        return AlertScore(job_name=job_name, score=round(raw, 4), factors=factors)

    failure_count = sum(1 for e in entries if not e.succeeded)
    failure_rate = failure_count / runs

    stats: Optional[BaselineStats] = baseline_store.stats_for(job_name)
    consec = stats.consecutive_failures if stats else 0

    factors = ScoreFactors(
        failure_rate=failure_rate,
        consecutive_failures=consec,
        is_anomalous=is_anomalous,
        runs_available=runs,
    )

    raw = (
        _W_FAILURE_RATE * failure_rate
        + _W_CONSEC * _consec_component(consec)
        + _W_ANOMALY * (1.0 if is_anomalous else 0.0)
    )
    return AlertScore(job_name=job_name, score=round(min(raw, 1.0), 4), factors=factors)
