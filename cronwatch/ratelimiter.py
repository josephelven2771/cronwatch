"""Rate limiter for outbound alerts to prevent notification floods."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class _BucketState:
    count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RateLimitPolicy:
    """Defines how many alerts are allowed per window."""
    max_alerts: int = 5
    window_seconds: int = 3600  # 1 hour

    @property
    def window(self) -> timedelta:
        return timedelta(seconds=self.window_seconds)


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: datetime

    def __bool__(self) -> bool:
        return self.allowed


class RateLimiter:
    """Tracks per-job alert counts within a rolling time window."""

    def __init__(self, policy: RateLimitPolicy) -> None:
        self._policy = policy
        self._buckets: Dict[str, _BucketState] = {}

    def _bucket(self, key: str) -> _BucketState:
        now = datetime.utcnow()
        state = self._buckets.get(key)
        if state is None:
            state = _BucketState(window_start=now)
            self._buckets[key] = state
        elif now - state.window_start >= self._policy.window:
            state.count = 0
            state.window_start = now
        return state

    def check(self, key: str) -> RateLimitResult:
        """Return whether an alert for *key* is currently allowed."""
        state = self._bucket(key)
        reset_at = state.window_start + self._policy.window
        allowed = state.count < self._policy.max_alerts
        remaining = max(0, self._policy.max_alerts - state.count)
        return RateLimitResult(allowed=allowed, remaining=remaining, reset_at=reset_at)

    def record(self, key: str) -> None:
        """Increment the alert counter for *key*."""
        self._bucket(key).count += 1

    def allow(self, key: str) -> bool:
        """Convenience: check and, if allowed, record the alert in one call."""
        result = self.check(key)
        if result.allowed:
            self.record(key)
        return result.allowed

    def reset(self, key: str) -> None:
        """Manually clear the bucket for *key* (useful in tests)."""
        self._buckets.pop(key, None)
