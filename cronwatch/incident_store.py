"""Persist and load IncidentTracker state as newline-delimited JSON."""
from __future__ import annotations

import json
from pathlib import Path

from cronwatch.incident import Incident, IncidentTracker


def save_incidents(tracker: IncidentTracker, path: Path) -> None:
    """Write all incidents (open and closed) to *path* as NDJSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for inc in tracker.all_incidents():
            fh.write(json.dumps(inc.to_dict()) + "\n")


def load_incidents(path: Path) -> IncidentTracker:
    """Reconstruct an IncidentTracker from *path*.

    Returns an empty tracker if the file does not exist.
    """
    tracker = IncidentTracker()
    if not path.exists():
        return tracker

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            inc = Incident.from_dict(json.loads(line))
            # Restore into internal dict; last entry per job_name wins,
            # which matches the single-active-incident-per-job model.
            tracker._incidents[inc.job_name] = inc

    return tracker
