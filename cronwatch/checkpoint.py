"""Checkpoint module: persist and compare job execution state across runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _from_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


@dataclass
class JobCheckpoint:
    job_name: str
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    total_runs: int = 0

    def record_success(self) -> None:
        self.last_success = _utcnow()
        self.consecutive_failures = 0
        self.total_runs += 1

    def record_failure(self) -> None:
        self.last_failure = _utcnow()
        self.consecutive_failures += 1
        self.total_runs += 1

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_success": _iso(self.last_success) if self.last_success else None,
            "last_failure": _iso(self.last_failure) if self.last_failure else None,
            "consecutive_failures": self.consecutive_failures,
            "total_runs": self.total_runs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobCheckpoint":
        return cls(
            job_name=data["job_name"],
            last_success=_from_iso(data["last_success"]) if data.get("last_success") else None,
            last_failure=_from_iso(data["last_failure"]) if data.get("last_failure") else None,
            consecutive_failures=data.get("consecutive_failures", 0),
            total_runs=data.get("total_runs", 0),
        )


@dataclass
class CheckpointStore:
    _path: Path
    _data: Dict[str, JobCheckpoint] = field(default_factory=dict)

    def get(self, job_name: str) -> Optional[JobCheckpoint]:
        return self._data.get(job_name)

    def set(self, cp: JobCheckpoint) -> None:
        self._data[cp.job_name] = cp

    def get_or_create(self, job_name: str) -> JobCheckpoint:
        if job_name not in self._data:
            self._data[job_name] = JobCheckpoint(job_name=job_name)
        return self._data[job_name]

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: cp.to_dict() for name, cp in self._data.items()}
        self._path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> "CheckpointStore":
        store = cls(_path=path)
        if path.exists():
            raw = json.loads(path.read_text())
            store._data = {name: JobCheckpoint.from_dict(v) for name, v in raw.items()}
        return store
