"""Generate per-tag summary reports."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from cronwatch.tagger import group_by_tag
from cronwatch.history import HistoryEntry


@dataclass
class TagSummary:
    tag: str
    total: int
    failures: int
    job_names: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 1.0
        return (self.total - self.failures) / self.total

    def __str__(self) -> str:
        icon = "✓" if self.failures == 0 else "✗"
        return (
            f"[{icon}] {self.tag}: {self.total} runs, "
            f"{self.failures} failures "
            f"({self.success_rate:.0%} success)"
        )


def build_tag_report(entries: List[HistoryEntry]) -> Dict[str, TagSummary]:
    """Return a TagSummary for every tag found in entries."""
    groups = group_by_tag(entries)
    report: Dict[str, TagSummary] = {}
    for tag, tag_entries in groups.items():
        failures = sum(
            1 for e in tag_entries
            if hasattr(e, 'exit_code') and e.exit_code not in (None, 0)
        )
        job_names = sorted({e.job_name for e in tag_entries})
        report[tag] = TagSummary(
            tag=tag,
            total=len(tag_entries),
            failures=failures,
            job_names=job_names,
        )
    return report
