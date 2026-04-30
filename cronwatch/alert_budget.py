"""Alert budget tracking — limits total alerts fired within a rolling window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BudgetPolicy:
    max_alerts: int          # maximum alerts allowed in the window
    window_seconds: int      # rolling window length in seconds

    def __post_init__(self) -> None:
        if self.max_alerts < 1:
            raise ValueError("max_alerts must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


@dataclass
class BudgetResult:
    allowed: bool
    used: int
    remaining: int
    limit: int

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class _BudgetState:
    timestamps: List[datetime] = field(default_factory=list)

    def purge_before(self, cutoff: datetime) -> None:
        self.timestamps = [t for t in self.timestamps if t >= cutoff]


class AlertBudget:
    """Tracks how many alerts have been sent in a rolling window."""

    def __init__(self, policy: BudgetPolicy) -> None:
        self._policy = policy
        self._state: _BudgetState = _BudgetState()

    def _cutoff(self, now: datetime) -> datetime:
        return now - timedelta(seconds=self._policy.window_seconds)

    def check(self, now: datetime | None = None) -> BudgetResult:
        """Return whether another alert is allowed without recording it."""
        now = now or _utcnow()
        self._state.purge_before(self._cutoff(now))
        used = len(self._state.timestamps)
        remaining = max(0, self._policy.max_alerts - used)
        return BudgetResult(
            allowed=used < self._policy.max_alerts,
            used=used,
            remaining=remaining,
            limit=self._policy.max_alerts,
        )

    def record(self, now: datetime | None = None) -> BudgetResult:
        """Record one alert and return the resulting budget state."""
        now = now or _utcnow()
        result = self.check(now)
        if result.allowed:
            self._state.timestamps.append(now)
        # Re-compute after possible append
        used = len(self._state.timestamps)
        remaining = max(0, self._policy.max_alerts - used)
        return BudgetResult(
            allowed=result.allowed,
            used=used,
            remaining=remaining,
            limit=self._policy.max_alerts,
        )

    def reset(self) -> None:
        """Clear all recorded timestamps."""
        self._state = _BudgetState()
