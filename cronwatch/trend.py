"""Trend analysis for job run durations and failure rates over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.baseline import BaselineStats


@dataclass
class TrendResult:
    job_name: str
    direction: str          # 'improving', 'degrading', 'stable', 'unknown'
    duration_slope: Optional[float]  # seconds per run, positive = getting slower
    failure_rate_delta: Optional[float]  # change in failure rate (recent - baseline)
    note: str = ""

    def __bool__(self) -> bool:
        return self.direction == "degrading"


def _slope(values: List[float]) -> Optional[float]:
    """Return least-squares slope of a sequence of values, or None if too few."""
    n = len(values)
    if n < 2:
        return None
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def analyze_trend(
    job_name: str,
    recent_durations: List[float],
    baseline: Optional[BaselineStats],
    recent_failure_rate: Optional[float] = None,
    duration_slope_threshold: float = 5.0,
) -> TrendResult:
    """Compare recent run durations against baseline to detect trends.

    Args:
        job_name: Name of the cron job.
        recent_durations: Ordered list of recent run durations (seconds).
        baseline: Baseline statistics for the job, or None if unavailable.
        recent_failure_rate: Failure rate over the recent window (0-1), optional.
        duration_slope_threshold: Slope (sec/run) above which we flag degradation.
    """
    slope = _slope(recent_durations)
    failure_rate_delta: Optional[float] = None

    if baseline is not None and recent_failure_rate is not None:
        failure_rate_delta = recent_failure_rate - baseline.failure_rate

    if slope is None:
        return TrendResult(
            job_name=job_name,
            direction="unknown",
            duration_slope=None,
            failure_rate_delta=failure_rate_delta,
            note="insufficient data",
        )

    degrading = (
        slope > duration_slope_threshold
        or (failure_rate_delta is not None and failure_rate_delta > 0.1)
    )
    improving = (
        slope < -duration_slope_threshold
        and (failure_rate_delta is None or failure_rate_delta <= 0)
    )

    direction = "degrading" if degrading else ("improving" if improving else "stable")
    notes = []
    if slope > duration_slope_threshold:
        notes.append(f"duration increasing ~{slope:.1f}s/run")
    if failure_rate_delta is not None and failure_rate_delta > 0.1:
        notes.append(f"failure rate up {failure_rate_delta * 100:.1f}%")

    return TrendResult(
        job_name=job_name,
        direction=direction,
        duration_slope=slope,
        failure_rate_delta=failure_rate_delta,
        note="; ".join(notes),
    )
