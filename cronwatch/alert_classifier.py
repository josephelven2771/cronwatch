"""Classify alerts by severity based on job health signals and history."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from cronwatch.history import HistoryEntry


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ClassificationResult:
    job_name: str
    severity: Severity
    reasons: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # noqa: D105
        return self.severity in (Severity.HIGH, Severity.CRITICAL)

    def __str__(self) -> str:  # noqa: D105
        tag = self.severity.value.upper()
        return f"[{tag}] {self.job_name}: {'; '.join(self.reasons) or 'no issues'}"


def classify(
    job_name: str,
    entry: HistoryEntry,
    consecutive_failures: int = 0,
    failure_rate: Optional[float] = None,
) -> ClassificationResult:
    """Return a ClassificationResult for *entry* based on contextual signals."""
    reasons: List[str] = []
    score = 0

    if not entry.succeeded:
        reasons.append("job failed")
        score += 2

    if consecutive_failures >= 5:
        reasons.append(f"{consecutive_failures} consecutive failures")
        score += 3
    elif consecutive_failures >= 2:
        reasons.append(f"{consecutive_failures} consecutive failures")
        score += 1

    if failure_rate is not None:
        if failure_rate >= 0.75:
            reasons.append(f"failure rate {failure_rate:.0%}")
            score += 3
        elif failure_rate >= 0.4:
            reasons.append(f"failure rate {failure_rate:.0%}")
            score += 1

    if score >= 5:
        severity = Severity.CRITICAL
    elif score >= 3:
        severity = Severity.HIGH
    elif score >= 1:
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    return ClassificationResult(job_name=job_name, severity=severity, reasons=reasons)
