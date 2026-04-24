"""alert_suppressor.py — Suppress duplicate alerts within a configurable window.

Combines the Silencer, Cooldown, and Deduplicator to provide a single
decision point: should this alert actually fire?
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cronwatch.silencer import Silencer
from cronwatch.cooldown import CooldownTracker
from cronwatch.deduplicator import Deduplicator


@dataclass
class SuppressionResult:
    allowed: bool
    reason: str  # 'allowed', 'silenced', 'cooldown', 'duplicate'

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class AlertSuppressor:
    silencer: Silencer
    cooldown: CooldownTracker
    deduplicator: Deduplicator
    _suppressed_count: int = field(default=0, init=False)

    def check(self, job_name: str, message: str, now: Optional[datetime] = None) -> SuppressionResult:
        """Return a SuppressionResult indicating whether the alert should fire."""
        if now is None:
            now = datetime.now(timezone.utc)

        if self.silencer.is_silenced(job_name, now):
            self._suppressed_count += 1
            return SuppressionResult(allowed=False, reason="silenced")

        if not self.cooldown.can_alert(job_name, now):
            self._suppressed_count += 1
            return SuppressionResult(allowed=False, reason="cooldown")

        if self.deduplicator.is_duplicate(job_name, message, now):
            self._suppressed_count += 1
            return SuppressionResult(allowed=False, reason="duplicate")

        return SuppressionResult(allowed=True, reason="allowed")

    def record(self, job_name: str, message: str, now: Optional[datetime] = None) -> None:
        """Record that an alert was sent so future duplicates are suppressed."""
        if now is None:
            now = datetime.now(timezone.utc)
        self.cooldown.record(job_name, now)
        self.deduplicator.record(job_name, message, now)

    @property
    def suppressed_count(self) -> int:
        return self._suppressed_count
