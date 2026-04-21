"""Incident tracking: open, update, and resolve incidents for failing jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Incident:
    job_name: str
    incident_id: str
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    failure_count: int = 1
    last_failure_at: Optional[datetime] = None
    notes: str = ""

    @property
    def is_open(self) -> bool:
        return self.resolved_at is None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "incident_id": self.incident_id,
            "opened_at": self.opened_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "failure_count": self.failure_count,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d: dict) -> "Incident":
        def _parse(v: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(v) if v else None

        return Incident(
            job_name=d["job_name"],
            incident_id=d["incident_id"],
            opened_at=datetime.fromisoformat(d["opened_at"]),
            resolved_at=_parse(d.get("resolved_at")),
            failure_count=d.get("failure_count", 1),
            last_failure_at=_parse(d.get("last_failure_at")),
            notes=d.get("notes", ""),
        )


class IncidentTracker:
    """Manages open/closed incidents keyed by job name."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}

    def open_or_update(self, job_name: str) -> Incident:
        """Open a new incident or increment an existing open one."""
        now = _utcnow()
        if job_name in self._incidents and self._incidents[job_name].is_open:
            inc = self._incidents[job_name]
            inc.failure_count += 1
            inc.last_failure_at = now
        else:
            inc = Incident(
                job_name=job_name,
                incident_id=str(uuid.uuid4()),
                opened_at=now,
                last_failure_at=now,
            )
            self._incidents[job_name] = inc
        return inc

    def resolve(self, job_name: str) -> Optional[Incident]:
        """Mark the open incident for job_name as resolved."""
        inc = self._incidents.get(job_name)
        if inc and inc.is_open:
            inc.resolved_at = _utcnow()
            return inc
        return None

    def get(self, job_name: str) -> Optional[Incident]:
        return self._incidents.get(job_name)

    def open_incidents(self) -> list[Incident]:
        return [i for i in self._incidents.values() if i.is_open]

    def all_incidents(self) -> list[Incident]:
        return list(self._incidents.values())
