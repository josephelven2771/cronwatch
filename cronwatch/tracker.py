"""Job execution tracker — records job runs and detects missed/failed jobs."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cronwatch.config import JobConfig


@dataclass
class JobRun:
    job_name: str
    started_at: float
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    output: str = ""

    @property
    def duration(self) -> Optional[float]:
        if self.finished_at is not None:
            return self.finished_at - self.started_at
        return None

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return self.exit_code is not None and self.exit_code != 0


class JobTracker:
    """Tracks job runs and evaluates health against job config."""

    def __init__(self) -> None:
        self._runs: Dict[str, List[JobRun]] = {}

    def record_start(self, job_name: str) -> JobRun:
        run = JobRun(job_name=job_name, started_at=time.time())
        self._runs.setdefault(job_name, []).append(run)
        return run

    def record_finish(self, run: JobRun, exit_code: int, output: str = "") -> None:
        run.finished_at = time.time()
        run.exit_code = exit_code
        run.output = output

    def last_run(self, job_name: str) -> Optional[JobRun]:
        runs = self._runs.get(job_name, [])
        return runs[-1] if runs else None

    def is_overdue(self, job: JobConfig) -> bool:
        """Return True if the job hasn't run within its expected interval."""
        run = self.last_run(job.name)
        if run is None:
            return True
        elapsed = time.time() - run.started_at
        return elapsed > job.max_interval_seconds

    def all_runs(self, job_name: str) -> List[JobRun]:
        return list(self._runs.get(job_name, []))
