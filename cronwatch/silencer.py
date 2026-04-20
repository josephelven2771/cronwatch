"""Silence (suppress) alerts for specific jobs during maintenance windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SilenceWindow:
    """A time window during which alerts for a job are suppressed."""

    job_name: str
    start: datetime
    end: datetime
    reason: str = ""

    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Return True if the silence window covers *at* (default: now)."""
        now = at or datetime.now(tz=timezone.utc)
        return self.start <= now <= self.end

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SilenceWindow":
        return cls(
            job_name=data["job_name"],
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            reason=data.get("reason", ""),
        )


@dataclass
class Silencer:
    """Manages a collection of silence windows."""

    _windows: List[SilenceWindow] = field(default_factory=list)

    def add(self, window: SilenceWindow) -> None:
        """Register a silence window."""
        self._windows.append(window)

    def remove(self, job_name: str) -> int:
        """Remove all windows for *job_name*. Returns the number removed."""
        before = len(self._windows)
        self._windows = [w for w in self._windows if w.job_name != job_name]
        return before - len(self._windows)

    def is_silenced(self, job_name: str, at: Optional[datetime] = None) -> bool:
        """Return True if *job_name* has an active silence window."""
        return any(
            w.job_name == job_name and w.is_active(at)
            for w in self._windows
        )

    def active_windows(self, at: Optional[datetime] = None) -> List[SilenceWindow]:
        """Return all currently active windows."""
        return [w for w in self._windows if w.is_active(at)]

    def all_windows(self) -> List[SilenceWindow]:
        return list(self._windows)

    def to_dict(self) -> Dict[str, list]:
        return {"windows": [w.to_dict() for w in self._windows]}

    @classmethod
    def from_dict(cls, data: dict) -> "Silencer":
        silencer = cls()
        for entry in data.get("windows", []):
            silencer.add(SilenceWindow.from_dict(entry))
        return silencer
