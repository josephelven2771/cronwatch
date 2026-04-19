"""High-level helper used by the CLI `run` subcommand."""
from __future__ import annotations

from typing import Optional

from cronwatch.alerts import dispatch_alert
from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore
from cronwatch.notifier import Notifier
from cronwatch.runner import RunResult, run_job


def execute_named_job(
    job_name: str,
    cfg: CronwatchConfig,
    store: HistoryStore,
    notifier: Optional[Notifier] = None,
) -> RunResult:
    """Look up *job_name* in *cfg*, run it, and dispatch an alert on failure."""
    job = next((j for j in cfg.jobs if j.name == job_name), None)
    if job is None:
        raise ValueError(f"No job named {job_name!r} in configuration.")

    result = run_job(job, store)

    if not result.succeeded:
        message = (
            f"Job '{job_name}' failed with exit code {result.exit_code}.\n"
            f"{result.stderr.strip()}"
        )
        if notifier is not None:
            if notifier.should_notify(job_name, status="failed"):
                dispatch_alert(cfg.alerts, subject=f"cronwatch: {job_name} failed", body=message)
                notifier.mark_notified(job_name, status="failed")
        else:
            dispatch_alert(cfg.alerts, subject=f"cronwatch: {job_name} failed", body=message)

    return result
