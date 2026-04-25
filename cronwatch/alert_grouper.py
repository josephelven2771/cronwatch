"""alert_grouper.py – group related alerts by job tag or name prefix.

Grouping reduces noise by bundling multiple related alerts into a
single notification instead of firing one per entry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from cronwatch.history import HistoryEntry


@dataclass
class AlertGroup:
    """A collection of entries that share a grouping key."""

    key: str
    entries: List[HistoryEntry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)

    @property
    def failure_count(self) -> int:
        return sum(1 for e in self.entries if not e.succeeded)

    @property
    def summary(self) -> str:
        total = self.size
        failures = self.failure_count
        if failures == 0:
            return f"[{self.key}] {total} job(s) – all healthy"
        return f"[{self.key}] {total} job(s) – {failures} failure(s)"

    def __bool__(self) -> bool:  # truthy when there is at least one entry
        return self.size > 0


GroupKeyFn = Callable[[HistoryEntry], str]


def _default_key(entry: HistoryEntry) -> str:
    """Group by the first dot-separated segment of the job name."""
    return entry.job_name.split(".")[0]


class AlertGrouper:
    """Accumulate entries and expose them as named groups."""

    def __init__(self, key_fn: Optional[GroupKeyFn] = None) -> None:
        self._key_fn: GroupKeyFn = key_fn or _default_key
        self._groups: Dict[str, AlertGroup] = {}

    # ------------------------------------------------------------------
    def add(self, entry: HistoryEntry) -> AlertGroup:
        """Add *entry* to the appropriate group and return that group."""
        key = self._key_fn(entry)
        if key not in self._groups:
            self._groups[key] = AlertGroup(key=key)
        self._groups[key].entries.append(entry)
        return self._groups[key]

    def group(self, key: str) -> Optional[AlertGroup]:
        return self._groups.get(key)

    def all_groups(self) -> List[AlertGroup]:
        return list(self._groups.values())

    def problem_groups(self) -> List[AlertGroup]:
        """Return only groups that contain at least one failure."""
        return [g for g in self._groups.values() if g.failure_count > 0]

    def clear(self) -> None:
        self._groups.clear()
