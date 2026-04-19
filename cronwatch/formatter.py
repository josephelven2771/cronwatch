"""Format job history entries and digests for human-readable output."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from cronwatch.history import HistoryEntry


DATE_FMT = "%Y-%m-%d %H:%M:%S UTC"


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(DATE_FMT)


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs}s"


def format_entry(entry: HistoryEntry) -> str:
    """Return a single-line summary for a history entry."""
    icon = "✓" if entry.succeeded else "✗"
    started = _fmt_dt(entry.started_at)
    duration = _fmt_duration(entry.duration_seconds)
    exit_info = f"exit={entry.exit_code}" if entry.exit_code is not None else "no exit code"
    return f"[{icon}] {entry.job_name}  started={started}  duration={duration}  {exit_info}"


def format_entries(entries: List[HistoryEntry], *, title: str = "Job History") -> str:
    """Return a formatted block for a list of entries."""
    lines = [f"=== {title} ==="]
    if not entries:
        lines.append("  (no entries)")
    else:
        for e in entries:
            lines.append(f"  {format_entry(e)}")
    return "\n".join(lines)


def format_failure_summary(entries: List[HistoryEntry]) -> str:
    """Return a short failure-only summary."""
    failures = [e for e in entries if not e.succeeded]
    if not failures:
        return "No failures recorded."
    lines = [f"{len(failures)} failure(s) detected:"]
    for e in failures:
        lines.append(f"  - {format_entry(e)}")
    return "\n".join(lines)
