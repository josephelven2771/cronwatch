"""alert_muter.py — Mute alerts for specific jobs or tags for a fixed duration.

Provides a simple mute registry that suppresses alerts during a defined
time window.  Unlike the full Silencer (which persists windows), the
AlertMuter is an in-process, lightweight mechanism intended for use in
pipelines where temporary suppression is needed without disk I/O.

Typical usage::

    muter = AlertMuter()
    muter.mute("backup-db", duration_minutes=30)

    result = muter.check("backup-db")
    if not result:
        send_alert(...)
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclasses.dataclass
class MuteEntry:
    """Represents an active mute for a single job or tag key."""

    key: str
    muted_at: datetime
    expires_at: datetime
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if the mute window is still in effect."""
        now = now or _utcnow()
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "muted_at": self.muted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "reason": self.reason,
        }


@dataclasses.dataclass
class MuteResult:
    """Outcome of a mute check."""

    key: str
    muted: bool
    entry: Optional[MuteEntry] = None

    def __bool__(self) -> bool:
        """True when the alert is *not* muted (i.e. allowed to fire)."""
        return not self.muted

    @property
    def reason(self) -> str:
        return self.entry.reason if self.entry else ""

    @property
    def expires_at(self) -> Optional[datetime]:
        return self.entry.expires_at if self.entry else None


class AlertMuter:
    """In-process registry of temporary alert mutes.

    Keys can be job names, tag strings, or any arbitrary identifier used
    elsewhere in the pipeline.  Expired entries are lazily removed on
    each *check* call.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, MuteEntry] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def mute(self, key: str, duration_minutes: int = 60, reason: str = "") -> MuteEntry:
        """Register a mute for *key* lasting *duration_minutes* minutes.

        If an entry already exists it is overwritten, effectively
        extending or resetting the mute window.
        """
        now = _utcnow()
        entry = MuteEntry(
            key=key,
            muted_at=now,
            expires_at=now + timedelta(minutes=duration_minutes),
            reason=reason,
        )
        self._entries[key] = entry
        return entry

    def unmute(self, key: str) -> bool:
        """Remove the mute for *key*.  Returns True if an entry existed."""
        return self._entries.pop(key, None) is not None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def check(self, key: str) -> MuteResult:
        """Return a MuteResult indicating whether *key* is currently muted."""
        now = _utcnow()
        entry = self._entries.get(key)
        if entry is None:
            return MuteResult(key=key, muted=False)
        if not entry.is_active(now):
            # Lazy expiry
            del self._entries[key]
            return MuteResult(key=key, muted=False)
        return MuteResult(key=key, muted=True, entry=entry)

    def active_keys(self) -> list[str]:
        """Return all keys that currently have an active mute."""
        now = _utcnow()
        return [k for k, e in self._entries.items() if e.is_active(now)]

    def clear_expired(self) -> int:
        """Purge all expired mute entries.  Returns the number removed."""
        now = _utcnow()
        expired = [k for k, e in self._entries.items() if not e.is_active(now)]
        for k in expired:
            del self._entries[k]
        return len(expired)
