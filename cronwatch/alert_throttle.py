"""Alert throttle: limits how many alerts can be sent per job within a rolling window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ThrottlePolicy:
    max_alerts: int = 5
    window_seconds: int = 3600

    @property
    def window(self) -> timedelta:
        return timedelta(seconds=self.window_seconds)


@dataclass
class ThrottleResult:
    allowed: bool
    job_name: str
    sent_in_window: int
    max_alerts: int
    reason: str = ""

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class _JobThrottleState:
    timestamps: List[datetime] = field(default_factory=list)

    def prune(self, cutoff: datetime) -> None:
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def count(self) -> int:
        return len(self.timestamps)

    def record(self, ts: datetime) -> None:
        self.timestamps.append(ts)


class AlertThrottle:
    """Tracks per-job alert counts within a rolling time window."""

    def __init__(self, policy: ThrottlePolicy | None = None) -> None:
        self._policy = policy or ThrottlePolicy()
        self._states: Dict[str, _JobThrottleState] = {}

    def _state_for(self, job_name: str) -> _JobThrottleState:
        if job_name not in self._states:
            self._states[job_name] = _JobThrottleState()
        return self._states[job_name]

    def check(self, job_name: str, now: datetime | None = None) -> ThrottleResult:
        """Return whether an alert for *job_name* is allowed right now."""
        now = now or _utcnow()
        cutoff = now - self._policy.window
        state = self._state_for(job_name)
        state.prune(cutoff)
        sent = state.count()
        if sent >= self._policy.max_alerts:
            return ThrottleResult(
                allowed=False,
                job_name=job_name,
                sent_in_window=sent,
                max_alerts=self._policy.max_alerts,
                reason=f"throttled: {sent}/{self._policy.max_alerts} alerts in window",
            )
        return ThrottleResult(
            allowed=True,
            job_name=job_name,
            sent_in_window=sent,
            max_alerts=self._policy.max_alerts,
        )

    def record(self, job_name: str, now: datetime | None = None) -> None:
        """Record that an alert was sent for *job_name*."""
        now = now or _utcnow()
        self._state_for(job_name).record(now)

    def reset(self, job_name: str) -> None:
        """Clear throttle state for *job_name*."""
        self._states.pop(job_name, None)
