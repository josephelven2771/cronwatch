"""Aggregate health evaluation for a single job across multiple signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.anomaly import AnomalyResult
from cronwatch.threshold import ThresholdResult
from cronwatch.trend import TrendResult
from cronwatch.window_checker import WindowResult


@dataclass
class HealthSignal:
    """A single named signal contributing to job health."""

    name: str
    ok: bool
    detail: str = ""


@dataclass
class JobHealthResult:
    """Aggregated health result for one job."""

    job_name: str
    signals: List[HealthSignal] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(s.ok for s in self.signals)

    @property
    def failing_signals(self) -> List[HealthSignal]:
        return [s for s in self.signals if not s.ok]

    def summary(self) -> str:
        if self.healthy:
            return f"{self.job_name}: healthy"
        parts = ", ".join(s.name for s in self.failing_signals)
        return f"{self.job_name}: unhealthy [{parts}]"

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "healthy": self.healthy,
            "signals": [
                {"name": s.name, "ok": s.ok, "detail": s.detail}
                for s in self.signals
            ],
        }


def evaluate_job_health(
    job_name: str,
    *,
    anomaly: Optional[AnomalyResult] = None,
    threshold: Optional[ThresholdResult] = None,
    trend: Optional[TrendResult] = None,
    window: Optional[WindowResult] = None,
) -> JobHealthResult:
    """Combine individual signal results into a single JobHealthResult."""
    result = JobHealthResult(job_name=job_name)

    if anomaly is not None:
        result.signals.append(
            HealthSignal(
                name="anomaly",
                ok=not bool(anomaly),
                detail=anomaly.detail if bool(anomaly) else "",
            )
        )

    if threshold is not None:
        result.signals.append(
            HealthSignal(
                name="threshold",
                ok=not bool(threshold),
                detail=threshold.detail if bool(threshold) else "",
            )
        )

    if trend is not None:
        result.signals.append(
            HealthSignal(
                name="trend",
                ok=not bool(trend),
                detail=trend.detail if bool(trend) else "",
            )
        )

    if window is not None:
        result.signals.append(
            HealthSignal(
                name="window",
                ok=bool(window),
                detail=window.detail if not bool(window) else "",
            )
        )

    return result
