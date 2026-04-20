"""Alert escalation: upgrade severity after repeated failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class EscalationPolicy:
    """How many consecutive failures before escalating."""
    threshold: int = 3          # failures before escalation
    cooldown_minutes: int = 60  # minutes before de-escalating


@dataclass
class _JobState:
    consecutive_failures: int = 0
    escalated_since: Optional[datetime] = None


@dataclass
class EscalationResult:
    job_name: str
    escalated: bool
    consecutive_failures: int
    escalated_since: Optional[datetime] = None

    def __bool__(self) -> bool:
        return self.escalated


class Escalator:
    """Tracks consecutive failures and decides when to escalate alerts."""

    def __init__(self, policy: EscalationPolicy) -> None:
        self._policy = policy
        self._states: Dict[str, _JobState] = {}

    def _state_for(self, job_name: str) -> _JobState:
        if job_name not in self._states:
            self._states[job_name] = _JobState()
        return self._states[job_name]

    def record_failure(self, job_name: str, now: Optional[datetime] = None) -> EscalationResult:
        """Record a failure; return whether the job is now escalated."""
        now = now or datetime.utcnow()
        state = self._state_for(job_name)
        state.consecutive_failures += 1

        if state.consecutive_failures >= self._policy.threshold and state.escalated_since is None:
            state.escalated_since = now

        return EscalationResult(
            job_name=job_name,
            escalated=state.escalated_since is not None,
            consecutive_failures=state.consecutive_failures,
            escalated_since=state.escalated_since,
        )

    def record_success(self, job_name: str, now: Optional[datetime] = None) -> None:
        """A success de-escalates the job after the cooldown has elapsed."""
        now = now or datetime.utcnow()
        state = self._state_for(job_name)
        cooldown = timedelta(minutes=self._policy.cooldown_minutes)
        if state.escalated_since is None or (now - state.escalated_since) >= cooldown:
            state.consecutive_failures = 0
            state.escalated_since = None

    def is_escalated(self, job_name: str) -> bool:
        return self._state_for(job_name).escalated_since is not None

    def reset(self, job_name: str) -> None:
        """Unconditionally reset state for a job."""
        self._states.pop(job_name, None)
