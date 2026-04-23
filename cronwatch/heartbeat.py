"""Heartbeat tracker — records periodic pings from cron jobs and
detects jobs that have gone silent beyond their expected interval."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class HeartbeatRecord:
    job_name: str
    last_ping: float          # unix timestamp
    interval_seconds: int     # expected max seconds between pings

    def is_overdue(self, now: Optional[float] = None) -> bool:
        """Return True if the job has not pinged within its interval."""
        now = now if now is not None else time.time()
        return (now - self.last_ping) > self.interval_seconds

    def seconds_overdue(self, now: Optional[float] = None) -> float:
        now = now if now is not None else time.time()
        overdue = now - self.last_ping - self.interval_seconds
        return max(overdue, 0.0)

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_ping": self.last_ping,
            "interval_seconds": self.interval_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HeartbeatRecord":
        return cls(
            job_name=data["job_name"],
            last_ping=float(data["last_ping"]),
            interval_seconds=int(data["interval_seconds"]),
        )


class HeartbeatStore:
    """Persist and retrieve heartbeat records as a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._records: Dict[str, HeartbeatRecord] = {}
        self._load()

    # ------------------------------------------------------------------
    def ping(self, job_name: str, interval_seconds: int,
             now: Optional[float] = None) -> HeartbeatRecord:
        """Record a ping for *job_name* and persist."""
        ts = now if now is not None else time.time()
        record = HeartbeatRecord(
            job_name=job_name,
            last_ping=ts,
            interval_seconds=interval_seconds,
        )
        self._records[job_name] = record
        self._save()
        return record

    def get(self, job_name: str) -> Optional[HeartbeatRecord]:
        return self._records.get(job_name)

    def all_overdue(self, now: Optional[float] = None) -> list[HeartbeatRecord]:
        """Return every record whose interval has been exceeded."""
        return [r for r in self._records.values() if r.is_overdue(now)]

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._path.exists():
            return
        raw = json.loads(self._path.read_text())
        self._records = {k: HeartbeatRecord.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._records.items()}, indent=2)
        )
