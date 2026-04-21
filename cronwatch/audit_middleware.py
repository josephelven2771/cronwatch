"""Middleware helpers that wrap alert dispatch and silencer checks with audit logging."""

from __future__ import annotations

from typing import Any, Optional

from cronwatch.audit_log import AuditLog
from cronwatch.history import HistoryEntry


class AuditMiddleware:
    """Wraps core cronwatch actions to emit audit log entries automatically."""

    def __init__(self, audit_log: AuditLog) -> None:
        self._log = audit_log

    # ------------------------------------------------------------------
    # Alert helpers
    # ------------------------------------------------------------------

    def record_alert_sent(self, entry: HistoryEntry, channel: str) -> None:
        """Call after an alert has been successfully dispatched."""
        detail = f"channel={channel} exit_code={entry.exit_code}"
        self._log.append(
            event="alert_sent",
            job_name=entry.job_name,
            detail=detail,
            tags=list(getattr(entry, "tags", None) or []),
        )

    def record_alert_suppressed(self, entry: HistoryEntry, reason: str) -> None:
        """Call when an alert was suppressed (rate-limit, silence, dedup)."""
        self._log.append(
            event="alert_suppressed",
            job_name=entry.job_name,
            detail=reason,
            tags=list(getattr(entry, "tags", None) or []),
        )

    # ------------------------------------------------------------------
    # Silence helpers
    # ------------------------------------------------------------------

    def record_silence_applied(self, job_name: str, window_id: str) -> None:
        """Call when a silence window prevents an alert for a job."""
        self._log.append(
            event="silence_applied",
            job_name=job_name,
            detail=f"window_id={window_id}",
        )

    # ------------------------------------------------------------------
    # Escalation helpers
    # ------------------------------------------------------------------

    def record_escalation(self, job_name: str, failure_count: int, level: int) -> None:
        """Call when an escalation threshold is crossed."""
        detail = f"failure_count={failure_count} level={level}"
        self._log.append(
            event="escalation_triggered",
            job_name=job_name,
            detail=detail,
        )

    # ------------------------------------------------------------------
    # Rate-limit helpers
    # ------------------------------------------------------------------

    def record_rate_limited(self, job_name: str, remaining: int, window_seconds: int) -> None:
        """Call when an alert is blocked by the rate limiter."""
        detail = f"remaining={remaining} window={window_seconds}s"
        self._log.append(
            event="rate_limited",
            job_name=job_name,
            detail=detail,
        )
