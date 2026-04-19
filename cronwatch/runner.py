"""Run a shell command as a tracked cron job and record the result."""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.history import HistoryStore
from cronwatch.tracker import JobTracker


@dataclass
class RunResult:
    job_name: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


def run_job(
    job: JobConfig,
    store: HistoryStore,
    tracker: Optional[JobTracker] = None,
    timeout: Optional[int] = None,
) -> RunResult:
    """Execute *job.command* in a subprocess, persist the outcome, and return a RunResult."""
    if tracker is None:
        tracker = JobTracker()

    job_run = tracker.record_start(job.name)
    start = time.monotonic()

    try:
        proc = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = ""
        stderr = f"Timed out after {exc.timeout}s"
    except Exception as exc:  # noqa: BLE001
        exit_code = 1
        stdout = ""
        stderr = str(exc)

    elapsed = time.monotonic() - start

    if exit_code == 0:
        tracker.record_finish(job_run, success=True)
    else:
        tracker.record_finish(job_run, success=False)

    store.record(
        job_name=job.name,
        succeeded=exit_code == 0,
        duration=elapsed,
        output=stdout + stderr,
    )

    return RunResult(
        job_name=job.name,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=elapsed,
    )
