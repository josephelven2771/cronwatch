"""Deduplicator: suppress repeated alerts for the same job failure."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class _SeenEntry:
    first_seen: datetime
    last_alerted: datetime
    alert_count: int = 1


@dataclass
class Deduplicator:
    """Track seen failure fingerprints to avoid duplicate alerts."""
    window_seconds: int = 3600
    _seen: Dict[str, _SeenEntry] = field(default_factory=dict, init=False)

    def _fingerprint(self, job_name: str, reason: str) -> str:
        return f"{job_name}:{reason}"

    def is_duplicate(self, job_name: str, reason: str, now: Optional[datetime] = None) -> bool:
        """Return True if this failure was already reported within the window."""
        now = now or datetime.utcnow()
        key = self._fingerprint(job_name, reason)
        entry = self._seen.get(key)
        if entry is None:
            return False
        age = (now - entry.last_alerted).total_seconds()
        return age < self.window_seconds

    def record(self, job_name: str, reason: str, now: Optional[datetime] = None) -> None:
        """Record that an alert was dispatched for this failure."""
        now = now or datetime.utcnow()
        key = self._fingerprint(job_name, reason)
        existing = self._seen.get(key)
        if existing is None:
            self._seen[key] = _SeenEntry(first_seen=now, last_alerted=now)
        else:
            existing.last_alerted = now
            existing.alert_count += 1

    def clear_expired(self, now: Optional[datetime] = None) -> int:
        """Remove entries older than the window. Returns count removed."""
        now = now or datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        expired = [k for k, v in self._seen.items() if v.last_alerted < cutoff]
        for k in expired:
            del self._seen[k]
        return len(expired)

    def reset(self, job_name: str, reason: str) -> None:
        """Manually clear a fingerprint so the next occurrence alerts."""
        key = self._fingerprint(job_name, reason)
        self._seen.pop(key, None)
