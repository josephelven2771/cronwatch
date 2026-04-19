"""Digest report: aggregate job statuses into a summary payload."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from cronwatch.reporter import JobStatus, Reporter
from cronwatch.config import CronwatchConfig


@dataclass
class DigestEntry:
    job_name: str
    status: str  # 'healthy' | 'missed' | 'failed'
    last_run: datetime | None
    summary: str


@dataclass
class Digest:
    generated_at: datetime
    entries: List[DigestEntry] = field(default_factory=list)

    @property
    def healthy_count(self) -> int:
        return sum(1 for e in self.entries if e.status == "healthy")

    @property
    def problem_count(self) -> int:
        return len(self.entries) - self.healthy_count

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "healthy": self.healthy_count,
            "problems": self.problem_count,
            "jobs": [
                {
                    "job": e.job_name,
                    "status": e.status,
                    "last_run": e.last_run.isoformat() if e.last_run else None,
                    "summary": e.summary,
                }
                for e in self.entries
            ],
        }


def build_digest(config: CronwatchConfig, reporter: Reporter) -> Digest:
    """Build a Digest from all configured jobs using the given Reporter."""
    entries: List[DigestEntry] = []
    for job in config.jobs:
        status: JobStatus = reporter.status(job)
        last_entry = reporter.store.last(job.name)
        entries.append(
            DigestEntry(
                job_name=job.name,
                status=status.value,
                last_run=last_entry.finished_at if last_entry else None,
                summary=reporter.summary_line(job),
            )
        )
    return Digest(generated_at=datetime.utcnow(), entries=entries)
