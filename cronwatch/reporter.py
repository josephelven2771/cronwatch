"""Generate human-readable status reports from job history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.history import HistoryStore
from cronwatch.config import CronwatchConfig


@dataclass
class JobStatus:
    name: str
    last_run: Optional[datetime]
    last_exit_code: Optional[int]
    last_duration: Optional[float]
    missed: bool

    @property
    def healthy(self) -> bool:
        return not self.missed and self.last_exit_code == 0

    def summary_line(self) -> str:
        state = "OK" if self.healthy else ("MISSED" if self.missed else "FAIL")
        if self.last_run:
            ts = self.last_run.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = "never"
        dur = f"{self.last_duration:.1f}s" if self.last_duration is not None else "--"
        return f"[{state:6}] {self.name:<30} last={ts}  duration={dur}  exit={self.last_exit_code}"


class Reporter:
    def __init__(self, config: CronwatchConfig, store: HistoryStore) -> None:
        self._config = config
        self._store = store

    def collect(self) -> List[JobStatus]:
        now = datetime.now(tz=timezone.utc)
        statuses: List[JobStatus] = []
        for job in self._config.jobs:
            entry = self._store.last(job.name)
            if entry is None:
                statuses.append(JobStatus(
                    name=job.name,
                    last_run=None,
                    last_exit_code=None,
                    last_duration=None,
                    missed=True,
                ))
                continue
            elapsed = (now - entry.started_at).total_seconds()
            missed = elapsed > job.expected_interval_seconds * 1.5
            statuses.append(JobStatus(
                name=job.name,
                last_run=entry.started_at,
                last_exit_code=entry.exit_code,
                last_duration=entry.duration_seconds,
                missed=missed,
            ))
        return statuses

    def render_text(self) -> str:
        statuses = self.collect()
        lines = ["cronwatch status report", "=" * 60]
        for s in statuses:
            lines.append(s.summary_line())
        healthy = sum(1 for s in statuses if s.healthy)
        lines.append("=" * 60)
        lines.append(f"{healthy}/{len(statuses)} jobs healthy")
        return "\n".join(lines)
