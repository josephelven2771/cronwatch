"""alert_sampler.py – probabilistic sampling for alert volume control.

Allows a fraction of alerts to pass through when the system is under high
alert load, preventing notification floods while still surfacing issues.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronwatch.history import HistoryEntry


@dataclass
class SamplePolicy:
    """Defines the sampling behaviour."""
    # Fraction of alerts to allow through (0.0 – 1.0).
    rate: float = 1.0
    # Only apply sampling when the per-check alert count exceeds this value.
    threshold: int = 0
    # Optional fixed seed for deterministic testing.
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError(f"rate must be between 0 and 1, got {self.rate}")
        if self.threshold < 0:
            raise ValueError("threshold must be >= 0")


@dataclass
class SampleResult:
    """Outcome of a sampling decision."""
    entry: HistoryEntry
    allowed: bool
    rate: float

    def __bool__(self) -> bool:  # noqa: D105
        return self.allowed


@dataclass
class AlertSampler:
    """Applies probabilistic sampling to a stream of alert candidates."""

    policy: SamplePolicy
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.policy.seed)

    # ------------------------------------------------------------------
    def sample(
        self,
        entries: List[HistoryEntry],
    ) -> List[SampleResult]:
        """Return a SampleResult for every entry.

        When the number of entries exceeds the policy threshold, each entry
        is independently accepted with probability *rate*.
        """
        apply_sampling = len(entries) > self.policy.threshold
        results: List[SampleResult] = []
        for entry in entries:
            if apply_sampling:
                allowed = self._rng.random() < self.policy.rate
            else:
                allowed = True
            results.append(SampleResult(entry=entry, allowed=allowed, rate=self.policy.rate))
        return results

    def filter(
        self,
        entries: List[HistoryEntry],
    ) -> List[HistoryEntry]:
        """Convenience wrapper – return only the allowed entries."""
        return [r.entry for r in self.sample(entries) if r.allowed]
