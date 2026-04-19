"""Filter history entries by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from cronwatch.history import HistoryEntry


@dataclass
class FilterCriteria:
    job_name: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    succeeded_only: bool = False
    failed_only: bool = False
    limit: Optional[int] = None


def filter_entries(
    entries: Iterable[HistoryEntry],
    criteria: FilterCriteria,
) -> List[HistoryEntry]:
    """Return entries matching *criteria* in chronological order."""
    results: List[HistoryEntry] = []

    for entry in entries:
        if criteria.job_name and entry.job_name != criteria.job_name:
            continue
        if criteria.since and entry.started_at < criteria.since:
            continue
        if criteria.until and entry.started_at > criteria.until:
            continue
        if criteria.succeeded_only and not entry.succeeded:
            continue
        if criteria.failed_only and entry.succeeded:
            continue
        results.append(entry)

    results.sort(key=lambda e: e.started_at)

    if criteria.limit is not None:
        results = results[-criteria.limit :]

    return results


def filter_by_job(entries: Iterable[HistoryEntry], job_name: str) -> List[HistoryEntry]:
    """Convenience wrapper: return all entries for a single job."""
    return filter_entries(entries, FilterCriteria(job_name=job_name))


def filter_failures(entries: Iterable[HistoryEntry]) -> List[HistoryEntry]:
    """Convenience wrapper: return only failed entries."""
    return filter_entries(entries, FilterCriteria(failed_only=True))
