"""Persist and restore CooldownTracker state to/from a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from cronwatch.cooldown import CooldownEntry, CooldownTracker


def save_cooldown(tracker: CooldownTracker, path: Union[str, Path]) -> None:
    """Serialise tracker state to a JSON file (one entry per job)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "window_seconds": tracker.window_seconds,
        "entries": [e.to_dict() for e in tracker._entries.values()],
    }
    path.write_text(json.dumps(data, indent=2))


def load_cooldown(path: Union[str, Path], window_seconds: int = 3600) -> CooldownTracker:
    """Load a CooldownTracker from a JSON file, or return an empty tracker."""
    path = Path(path)
    if not path.exists():
        return CooldownTracker(window_seconds=window_seconds)

    raw = json.loads(path.read_text())
    tracker = CooldownTracker(window_seconds=raw.get("window_seconds", window_seconds))
    for entry_data in raw.get("entries", []):
        entry = CooldownEntry.from_dict(entry_data)
        tracker._entries[entry.job_name] = entry
    return tracker
