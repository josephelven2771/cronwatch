"""Append-only audit log for cronwatch events (alerts sent, silences applied, escalations)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditEntry:
    timestamp: str
    event: str          # e.g. "alert_sent", "silence_applied", "escalation_triggered"
    job_name: str
    detail: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event": self.event,
            "job_name": self.job_name,
            "detail": self.detail,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditEntry":
        return AuditEntry(
            timestamp=d["timestamp"],
            event=d["event"],
            job_name=d["job_name"],
            detail=d.get("detail", ""),
            tags=d.get("tags", []),
        )


class AuditLog:
    """Reads and writes audit log entries to a newline-delimited JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def append(self, event: str, job_name: str, detail: str = "", tags: Optional[List[str]] = None) -> AuditEntry:
        entry = AuditEntry(
            timestamp=_now_iso(),
            event=event,
            job_name=job_name,
            detail=detail,
            tags=tags or [],
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def read_all(self) -> List[AuditEntry]:
        if not self._path.exists():
            return []
        entries: List[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(AuditEntry.from_dict(json.loads(line)))
        return entries

    def read_for_job(self, job_name: str) -> List[AuditEntry]:
        return [e for e in self.read_all() if e.job_name == job_name]

    def read_by_event(self, event: str) -> List[AuditEntry]:
        return [e for e in self.read_all() if e.event == event]
