"""Point-in-time snapshot of all job statuses for diffing and reporting."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class JobSnapshot:
    job_name: str
    last_run: Optional[datetime]
    last_exit_code: Optional[int]
    last_duration: Optional[float]
    success_count: int
    failure_count: int

    def is_healthy(self) -> bool:
        return self.last_exit_code == 0

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_exit_code": self.last_exit_code,
            "last_duration": self.last_duration,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobSnapshot":
        last_run = None
        if data.get("last_run"):
            last_run = datetime.fromisoformat(data["last_run"])
        return cls(
            job_name=data["job_name"],
            last_run=last_run,
            last_exit_code=data.get("last_exit_code"),
            last_duration=data.get("last_duration"),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
        )


@dataclass
class Snapshot:
    taken_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    jobs: Dict[str, JobSnapshot] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "taken_at": self.taken_at.isoformat(),
            "jobs": {name: snap.to_dict() for name, snap in self.jobs.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        taken_at = datetime.fromisoformat(data["taken_at"])
        jobs = {
            name: JobSnapshot.from_dict(snap)
            for name, snap in data.get("jobs", {}).items()
        }
        return cls(taken_at=taken_at, jobs=jobs)


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2))


def load_snapshot(path: Path) -> Optional[Snapshot]:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Snapshot.from_dict(data)
