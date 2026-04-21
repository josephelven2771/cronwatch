"""Threshold-based alerting: flag jobs whose failure rate or duration
exceeds configurable limits."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cronwatch.baseline import BaselineStats


@dataclass
class ThresholdPolicy:
    """Limits that trigger a threshold breach."""
    max_failure_rate: float = 0.5   # 0.0 – 1.0
    max_avg_duration: Optional[float] = None  # seconds; None = no limit
    min_runs: int = 3               # require at least this many runs


@dataclass
class ThresholdResult:
    """Outcome of a single threshold check."""
    job_name: str
    breached: bool
    failure_rate: Optional[float]
    avg_duration: Optional[float]
    reasons: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return self.breached


def check_threshold(
    job_name: str,
    stats: Optional[BaselineStats],
    policy: ThresholdPolicy,
) -> ThresholdResult:
    """Return a ThresholdResult for *job_name* given its baseline *stats*."""
    if stats is None or stats.run_count < policy.min_runs:
        return ThresholdResult(
            job_name=job_name,
            breached=False,
            failure_rate=None,
            avg_duration=None,
        )

    reasons: list[str] = []
    rate = stats.failure_rate()
    avg_dur = stats.avg_duration()

    if rate is not None and rate > policy.max_failure_rate:
        reasons.append(
            f"failure rate {rate:.1%} exceeds limit {policy.max_failure_rate:.1%}"
        )

    if (
        policy.max_avg_duration is not None
        and avg_dur is not None
        and avg_dur > policy.max_avg_duration
    ):
        reasons.append(
            f"avg duration {avg_dur:.1f}s exceeds limit {policy.max_avg_duration:.1f}s"
        )

    return ThresholdResult(
        job_name=job_name,
        breached=bool(reasons),
        failure_rate=rate,
        avg_duration=avg_dur,
        reasons=reasons,
    )
