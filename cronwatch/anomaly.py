"""Anomaly detection: flag job runs that deviate significantly from baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.baseline import BaselineStats


@dataclass
class AnomalyResult:
    job_name: str
    is_anomaly: bool
    reason: Optional[str]
    actual_duration: Optional[float]   # seconds
    expected_duration: Optional[float]  # seconds (baseline avg)
    z_score: Optional[float]

    def __bool__(self) -> bool:
        return self.is_anomaly


def _z_score(value: float, mean: float, stddev: float) -> Optional[float]:
    """Return z-score, or None when stddev is zero."""
    if stddev == 0.0:
        return None
    return (value - mean) / stddev


def detect_duration_anomaly(
    job_name: str,
    actual_duration: float,
    stats: Optional[BaselineStats],
    z_threshold: float = 3.0,
) -> AnomalyResult:
    """Return an AnomalyResult indicating whether *actual_duration* is anomalous.

    A run is anomalous when its z-score relative to the baseline mean/stddev
    exceeds *z_threshold* in either direction.
    """
    if stats is None or stats.run_count < 2:
        return AnomalyResult(
            job_name=job_name,
            is_anomaly=False,
            reason=None,
            actual_duration=actual_duration,
            expected_duration=None,
            z_score=None,
        )

    mean = stats.avg_duration
    stddev = stats.stddev_duration
    expected = mean
    z = _z_score(actual_duration, mean, stddev)

    if z is None:
        return AnomalyResult(
            job_name=job_name,
            is_anomaly=False,
            reason=None,
            actual_duration=actual_duration,
            expected_duration=expected,
            z_score=None,
        )

    if abs(z) >= z_threshold:
        direction = "longer" if z > 0 else "shorter"
        reason = (
            f"duration {actual_duration:.1f}s is {direction} than expected "
            f"{expected:.1f}s (z={z:.2f})"
        )
        return AnomalyResult(
            job_name=job_name,
            is_anomaly=True,
            reason=reason,
            actual_duration=actual_duration,
            expected_duration=expected,
            z_score=z,
        )

    return AnomalyResult(
        job_name=job_name,
        is_anomaly=False,
        reason=None,
        actual_duration=actual_duration,
        expected_duration=expected,
        z_score=z,
    )
