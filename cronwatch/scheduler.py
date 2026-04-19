"""Cron expression utilities for cronwatch."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from croniter import croniter


def next_run(expression: str, after: Optional[datetime] = None) -> datetime:
    """Return the next scheduled datetime for *expression*."""
    base = after or datetime.utcnow()
    return croniter(expression, base).get_next(datetime)


def prev_run(expression: str, before: Optional[datetime] = None) -> datetime:
    """Return the most recent scheduled datetime for *expression*."""
    base = before or datetime.utcnow()
    return croniter(expression, base).get_prev(datetime)


def is_overdue(expression: str, last_seen: Optional[datetime], grace_seconds: int = 60) -> bool:
    """Return True when the job described by *expression* is overdue.

    A job is overdue when the most-recently-expected run time has passed
    (plus *grace_seconds*) and *last_seen* is either absent or predates
    that expected run.
    """
    now = datetime.utcnow()
    expected = prev_run(expression, before=now)
    deadline = expected.timestamp() + grace_seconds
    if now.timestamp() < deadline:
        return False
    if last_seen is None:
        return True
    return last_seen < expected


def describe_schedule(expression: str) -> str:
    """Return a human-readable summary of *expression*."""
    now = datetime.utcnow()
    nxt = next_run(expression, after=now)
    prv = prev_run(expression, before=now)
    return (
        f"cron='{expression}'  "
        f"prev={prv.strftime('%Y-%m-%dT%H:%M:%SZ')}  "
        f"next={nxt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
