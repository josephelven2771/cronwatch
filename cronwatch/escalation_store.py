"""Persist escalation state across process restarts using JSON."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from cronwatch.escalator import Escalator, EscalationPolicy, _JobState

_DT_FMT = "%Y-%m-%dT%H:%M:%S"


def _dt_to_str(dt: datetime) -> str:
    return dt.strftime(_DT_FMT)


def _str_to_dt(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT)


def save_escalator(escalator: Escalator, path: Path) -> None:
    """Serialise escalator state to *path* as JSON."""
    data: Dict[str, Any] = {}
    for job_name, state in escalator._states.items():
        data[job_name] = {
            "consecutive_failures": state.consecutive_failures,
            "escalated_since": (
                _dt_to_str(state.escalated_since)
                if state.escalated_since is not None
                else None
            ),
        }
    path.write_text(json.dumps(data, indent=2))


def load_escalator(policy: EscalationPolicy, path: Path) -> Escalator:
    """Deserialise escalator state from *path*; returns fresh instance if missing."""
    escalator = Escalator(policy)
    if not path.exists():
        return escalator

    raw = json.loads(path.read_text())
    for job_name, entry in raw.items():
        state = _JobState(
            consecutive_failures=entry["consecutive_failures"],
            escalated_since=(
                _str_to_dt(entry["escalated_since"])
                if entry["escalated_since"] is not None
                else None
            ),
        )
        escalator._states[job_name] = state
    return escalator
