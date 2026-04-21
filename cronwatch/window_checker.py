"""window_checker.py — verify jobs ran within their expected time windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.history import HistoryStore


@dataclass
class WindowResult:
    job_name: str
    expected_start: datetime
    expected_end: datetime
    last_run: Optional[datetime]
    in_window: bool
    message: str

    def __bool__(self) -> bool:
        return self.in_window


def check_window(job: JobConfig, store: HistoryStore, now: Optional[datetime] = None) -> WindowResult:
    """Return a WindowResult indicating whether the job last ran inside its window."""
    if now is None:
        now = datetime.now(timezone.utc)

    window_start = job.window_start  # e.g. "02:00"
    window_end = job.window_end      # e.g. "04:00"

    def _parse(t: str) -> datetime:
        h, m = (int(x) for x in t.split(":"))
        return now.replace(hour=h, minute=m, second=0, microsecond=0)

    expected_start = _parse(window_start)
    expected_end = _parse(window_end)

    entry = store.last(job.name)
    last_run = entry.started_at if entry else None

    if last_run is None:
        return WindowResult(
            job_name=job.name,
            expected_start=expected_start,
            expected_end=expected_end,
            last_run=None,
            in_window=False,
            message=f"{job.name}: no history found",
        )

    in_window = expected_start <= last_run <= expected_end
    if in_window:
        msg = f"{job.name}: ran at {last_run.isoformat()} (within window)"
    else:
        msg = (
            f"{job.name}: ran at {last_run.isoformat()} "
            f"(outside window {window_start}–{window_end})"
        )

    return WindowResult(
        job_name=job.name,
        expected_start=expected_start,
        expected_end=expected_end,
        last_run=last_run,
        in_window=in_window,
        message=msg,
    )


@dataclass
class WindowChecker:
    config: CronwatchConfig
    store: HistoryStore
    results: List[WindowResult] = field(default_factory=list)

    def check_all(self, now: Optional[datetime] = None) -> List[WindowResult]:
        self.results = [
            check_window(job, self.store, now)
            for job in self.config.jobs
            if getattr(job, "window_start", None) and getattr(job, "window_end", None)
        ]
        return self.results

    @property
    def violations(self) -> List[WindowResult]:
        return [r for r in self.results if not r.in_window]
