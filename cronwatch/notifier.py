"""Notifier: rate-limit and deduplicate alert dispatching."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from cronwatch.alerts import dispatch_alert
from cronwatch.config import AlertConfig


@dataclass
class NotifierState:
    last_sent: float = 0.0
    count: int = 0


class Notifier:
    """Wraps dispatch_alert with per-job cooldown and repeat limiting."""

    def __init__(
        self,
        alert_config: AlertConfig,
        cooldown_seconds: int = 3600,
        max_repeats: Optional[int] = None,
    ) -> None:
        self.alert_config = alert_config
        self.cooldown_seconds = cooldown_seconds
        self.max_repeats = max_repeats
        self._state: Dict[str, NotifierState] = {}

    def _state_for(self, job_name: str) -> NotifierState:
        if job_name not in self._state:
            self._state[job_name] = NotifierState()
        return self._state[job_name]

    def should_notify(self, job_name: str) -> bool:
        state = self._state_for(job_name)
        if self.max_repeats is not None and state.count >= self.max_repeats:
            return False
        elapsed = time.time() - state.last_sent
        return elapsed >= self.cooldown_seconds

    def notify(self, job_name: str, subject: str, body: str) -> bool:
        """Send alert if cooldown allows. Returns True if sent."""
        if not self.should_notify(job_name):
            return False
        dispatch_alert(self.alert_config, subject, body)
        state = self._state_for(job_name)
        state.last_sent = time.time()
        state.count += 1
        return True

    def reset(self, job_name: str) -> None:
        """Reset state when a job recovers."""
        self._state.pop(job_name, None)
