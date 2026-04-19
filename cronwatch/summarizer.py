"""Summarizer: produce a human-readable summary report from a Digest."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronwatch.digest import Digest, DigestEntry


@dataclass
class SummaryReport:
    total: int
    healthy: int
    problems: int
    lines: List[str]

    def __str__(self) -> str:
        return "\n".join(self.lines)


def _status_icon(entry: DigestEntry) -> str:
    return "✓" if entry.healthy else "✗"


def _entry_line(entry: DigestEntry) -> str:
    icon = _status_icon(entry)
    name = entry.job_name
    note = entry.summary_line or "no runs recorded"
    return f"  [{icon}] {name}: {note}"


def build_summary(digest: Digest) -> SummaryReport:
    """Convert a Digest into a SummaryReport with formatted lines."""
    lines: List[str] = []
    total = len(digest.entries)
    healthy = digest.healthy_count()
    problems = digest.problem_count()

    lines.append(f"cronwatch report — {healthy}/{total} jobs healthy")
    lines.append("-" * 40)

    for entry in digest.entries:
        lines.append(_entry_line(entry))

    lines.append("-" * 40)
    if problems == 0:
        lines.append("All jobs are healthy.")
    else:
        lines.append(f"{problems} job(s) require attention.")

    return SummaryReport(
        total=total,
        healthy=healthy,
        problems=problems,
        lines=lines,
    )
