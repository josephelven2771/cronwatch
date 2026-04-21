"""Builds a Snapshot from the current HistoryStore state."""

from __future__ import annotations

from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.history import HistoryStore
from cronwatch.snapshot import JobSnapshot, Snapshot


def build_snapshot(config: CronwatchConfig, store: HistoryStore) -> Snapshot:
    """Create a Snapshot by inspecting each configured job's history."""
    snapshot = Snapshot()

    for job in config.jobs:
        entries = store.get(job.name)
        if not entries:
            snapshot.jobs[job.name] = JobSnapshot(
                job_name=job.name,
                last_run=None,
                last_exit_code=None,
                last_duration=None,
                success_count=0,
                failure_count=0,
            )
            continue

        latest = max(entries, key=lambda e: e.started_at)
        success_count = sum(1 for e in entries if e.exit_code == 0)
        failure_count = sum(1 for e in entries if e.exit_code != 0)

        snapshot.jobs[job.name] = JobSnapshot(
            job_name=job.name,
            last_run=latest.started_at,
            last_exit_code=latest.exit_code,
            last_duration=latest.duration,
            success_count=success_count,
            failure_count=failure_count,
        )

    return snapshot


def diff_snapshots(
    before: Snapshot, after: Snapshot
) -> dict:
    """Return a dict describing jobs that changed status between two snapshots."""
    changed = {}
    all_jobs = set(before.jobs) | set(after.jobs)
    for name in all_jobs:
        b = before.jobs.get(name)
        a = after.jobs.get(name)
        if b is None or a is None:
            changed[name] = {"before": b, "after": a}
            continue
        if b.last_exit_code != a.last_exit_code or b.last_run != a.last_run:
            changed[name] = {
                "before_exit_code": b.last_exit_code,
                "after_exit_code": a.last_exit_code,
                "before_last_run": b.last_run,
                "after_last_run": a.last_run,
            }
    return changed
