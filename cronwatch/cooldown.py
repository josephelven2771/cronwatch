"""Alert cooldown tracker: prevents repeated alerts for the same job within a time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CooldownEntry:
    job_name: str
    last_alerted: datetime
    alert_count: int = 1

    def is_cooled_down(self, window_seconds: int, now: Optional[datetime] = None) -> bool:
        """Return True if enough time has passed since the last alert."""
        now = now or _utcnow()
        elapsed = (now - self.last_alerted).total_seconds()
        return elapsed >= window_seconds

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_alerted": self.last_alerted.isoformat(),
            "alert_count": self.alert_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CooldownEntry":
        return cls(
            job_name=data["job_name"],
            last_alerted=datetime.fromisoformat(data["last_alerted"]),
            alert_count=data.get("alert_count", 1),
        )


@dataclass
class CooldownTracker:
    """Tracks per-job alert cooldowns."""

    window_seconds: int = 3600
    _entries: Dict[str, CooldownEntry] = field(default_factory=dict)

    def can_alert(self, job_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if the job is not currently in a cooldown period."""
        entry = self._entries.get(job_name)
        if entry is None:
            return True
        return entry.is_cooled_down(self.window_seconds, now=now)

    def record_alert(self, job_name: str, now: Optional[datetime] = None) -> CooldownEntry:
        """Record that an alert was sent for the given job."""
        now = now or _utcnow()
        existing = self._entries.get(job_name)
        if existing is None:
            entry = CooldownEntry(job_name=job_name, last_alerted=now)
        else:
            entry = CooldownEntry(
                job_name=job_name,
                last_alerted=now,
                alert_count=existing.alert_count + 1,
            )
        self._entries[job_name] = entry
        return entry

    def reset(self, job_name: str) -> None:
        """Clear cooldown state for a job (e.g., after recovery)."""
        self._entries.pop(job_name, None)

    def entry_for(self, job_name: str) -> Optional[CooldownEntry]:
        return self._entries.get(job_name)
