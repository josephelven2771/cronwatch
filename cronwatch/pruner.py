"""Prune old history entries to keep storage bounded."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.history import HistoryStore


def prune_by_age(store: HistoryStore, job_name: str, max_age_days: int) -> int:
    """Remove entries older than *max_age_days*. Returns count removed."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
    entries = store.all(job_name)
    kept = [e for e in entries if e.started_at >= cutoff]
    removed = len(entries) - len(kept)
    if removed:
        store._data[job_name] = [e.to_dict() for e in kept]
        store._save()
    return removed


def prune_by_count(store: HistoryStore, job_name: str, max_entries: int) -> int:
    """Keep only the *max_entries* most recent entries. Returns count removed."""
    entries = store.all(job_name)
    if len(entries) <= max_entries:
        return 0
    kept = entries[-max_entries:]
    removed = len(entries) - len(kept)
    store._data[job_name] = [e.to_dict() for e in kept]
    store._save()
    return removed


def prune_all(
    store: HistoryStore,
    max_age_days: Optional[int] = None,
    max_entries: Optional[int] = None,
) -> dict[str, int]:
    """Run pruning across all known jobs. Returns {job_name: removed_count}."""
    results: dict[str, int] = {}
    for job_name in list(store._data.keys()):
        removed = 0
        if max_age_days is not None:
            removed += prune_by_age(store, job_name, max_age_days)
        if max_entries is not None:
            removed += prune_by_count(store, job_name, max_entries)
        results[job_name] = removed
    return results
