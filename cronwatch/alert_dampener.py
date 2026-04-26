"""Alert dampener: suppress flapping alerts that recover quickly.

A job is considered 'flapping' when it alternates between healthy and
failing states faster than a configured stable_window.  While flapping,
alerts are dampened (suppressed) to avoid alert fatigue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DampenResult:
    job_name: str
    dampened: bool
    flap_count: int
    reason: str

    def __bool__(self) -> bool:  # True means the alert is ALLOWED through
        return not self.dampened


@dataclass
class _JobDampenState:
    transitions: List[datetime] = field(default_factory=list)
    last_status: Optional[bool] = None  # True = healthy, False = failing


class AlertDampener:
    """Suppress alerts for jobs whose status flaps within *stable_window*.

    Parameters
    ----------
    stable_window:
        Duration during which repeated status flips constitute flapping.
    flap_threshold:
        Minimum number of transitions within *stable_window* to be
        considered flapping.  Defaults to 3.
    """

    def __init__(
        self,
        stable_window: timedelta = timedelta(minutes=10),
        flap_threshold: int = 3,
    ) -> None:
        self._window = stable_window
        self._threshold = flap_threshold
        self._states: Dict[str, _JobDampenState] = {}

    # ------------------------------------------------------------------
    def _state_for(self, job_name: str) -> _JobDampenState:
        if job_name not in self._states:
            self._states[job_name] = _JobDampenState()
        return self._states[job_name]

    # ------------------------------------------------------------------
    def record(self, job_name: str, healthy: bool) -> None:
        """Record the latest status observation for *job_name*."""
        state = self._state_for(job_name)
        if state.last_status is not None and state.last_status != healthy:
            state.transitions.append(_utcnow())
        state.last_status = healthy

    # ------------------------------------------------------------------
    def check(self, job_name: str) -> DampenResult:
        """Return a DampenResult indicating whether the alert is dampened."""
        state = self._state_for(job_name)
        cutoff = _utcnow() - self._window
        recent = [t for t in state.transitions if t >= cutoff]
        # Prune old transitions
        state.transitions = recent

        flap_count = len(recent)
        if flap_count >= self._threshold:
            return DampenResult(
                job_name=job_name,
                dampened=True,
                flap_count=flap_count,
                reason=(
                    f"flapping: {flap_count} transitions in last "
                    f"{int(self._window.total_seconds())}s"
                ),
            )
        return DampenResult(
            job_name=job_name,
            dampened=False,
            flap_count=flap_count,
            reason="stable",
        )
