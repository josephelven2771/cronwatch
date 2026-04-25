"""alert_debouncer.py – suppress repeated alerts until a job has been healthy
for a configurable number of consecutive successes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class DebounceState:
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    armed: bool = True  # True = will fire on next failure


@dataclass
class DebounceResult:
    job_name: str
    should_alert: bool
    consecutive_failures: int
    reason: str

    def __bool__(self) -> bool:
        return self.should_alert


class AlertDebouncer:
    """Track per-job failure/success streaks and decide whether to fire an alert.

    An alert fires on the *first* failure after the job has been healthy (armed).
    Subsequent failures are suppressed until the job recovers with at least
    ``recovery_threshold`` consecutive successes, which re-arms it.

    Args:
        recovery_threshold: number of consecutive successes required to re-arm.
    """

    def __init__(self, recovery_threshold: int = 1) -> None:
        if recovery_threshold < 1:
            raise ValueError("recovery_threshold must be >= 1")
        self._recovery_threshold = recovery_threshold
        self._states: Dict[str, DebounceState] = {}

    def _state_for(self, job_name: str) -> DebounceState:
        if job_name not in self._states:
            self._states[job_name] = DebounceState()
        return self._states[job_name]

    def record_failure(self, job_name: str) -> DebounceResult:
        """Record a failure and return whether an alert should fire."""
        state = self._state_for(job_name)
        state.consecutive_failures += 1
        state.consecutive_successes = 0

        if state.armed:
            state.armed = False
            reason = "first failure after healthy period"
            return DebounceResult(job_name, True, state.consecutive_failures, reason)

        reason = f"debounced (failure #{state.consecutive_failures}, not yet recovered)"
        return DebounceResult(job_name, False, state.consecutive_failures, reason)

    def record_success(self, job_name: str) -> None:
        """Record a success; re-arm the debouncer once threshold is met."""
        state = self._state_for(job_name)
        state.consecutive_successes += 1
        state.consecutive_failures = 0
        if state.consecutive_successes >= self._recovery_threshold:
            state.armed = True

    def is_armed(self, job_name: str) -> bool:
        """Return True if the next failure will trigger an alert."""
        return self._state_for(job_name).armed

    def reset(self, job_name: str) -> None:
        """Remove all state for a job."""
        self._states.pop(job_name, None)
