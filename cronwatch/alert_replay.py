"""alert_replay.py — Replay suppressed or missed alerts from a time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

from cronwatch.audit_log import AuditEntry, AuditLog


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ReplayResult:
    replayed: List[AuditEntry] = field(default_factory=list)
    skipped: int = 0

    @property
    def count(self) -> int:
        return len(self.replayed)

    def __bool__(self) -> bool:
        return self.count > 0


def _is_suppressed_or_failed(entry: AuditEntry) -> bool:
    """Return True for entries that represent a suppressed or failed alert."""
    return entry.action in ("alert_suppressed", "alert_failed")


def replay_alerts(
    log: AuditLog,
    send_fn: Callable[[AuditEntry], bool],
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    job_name: Optional[str] = None,
    dry_run: bool = False,
) -> ReplayResult:
    """Replay suppressed/failed alerts from the audit log.

    Args:
        log:      AuditLog instance to read entries from.
        send_fn:  Callable that accepts an AuditEntry and returns True on success.
        since:    Only replay entries at or after this UTC datetime.
        until:    Only replay entries before or at this UTC datetime.
        job_name: Limit replay to a specific job name (matched against entry.job).
        dry_run:  If True, collect candidates but do not call send_fn.

    Returns:
        ReplayResult with replayed entries and skip count.
    """
    result = ReplayResult()

    for entry in log.read_all():
        if not _is_suppressed_or_failed(entry):
            result.skipped += 1
            continue

        ts = entry.timestamp
        if since and ts < since:
            result.skipped += 1
            continue
        if until and ts > until:
            result.skipped += 1
            continue
        if job_name and entry.job != job_name:
            result.skipped += 1
            continue

        if not dry_run:
            send_fn(entry)

        result.replayed.append(entry)

    return result


class AlertReplayer:
    """High-level helper that wraps replay_alerts with a fixed send function."""

    def __init__(self, log: AuditLog, send_fn: Callable[[AuditEntry], bool]) -> None:
        self._log = log
        self._send_fn = send_fn

    def run(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        job_name: Optional[str] = None,
        dry_run: bool = False,
    ) -> ReplayResult:
        return replay_alerts(
            self._log,
            self._send_fn,
            since=since,
            until=until,
            job_name=job_name,
            dry_run=dry_run,
        )
