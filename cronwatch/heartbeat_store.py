"""Persistence helpers for HeartbeatMonitor state.

Stores heartbeat records as a JSON file — one object per job — so that
overdue detection survives process restarts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from cronwatch.heartbeat import HeartbeatMonitor, HeartbeatRecord


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_raw(path: Path) -> Dict[str, dict]:
    """Return the raw JSON mapping stored at *path*, or an empty dict."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(path: Path, data: Dict[str, dict]) -> None:
    """Atomically write *data* to *path* as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_monitor(monitor: HeartbeatMonitor, path: Path) -> None:
    """Persist all heartbeat records held by *monitor* to *path*.

    Each job name maps to the serialised form produced by
    :meth:`HeartbeatRecord.to_dict`.

    Args:
        monitor: The :class:`HeartbeatMonitor` whose state should be saved.
        path:    Destination file path (created if it does not exist).
    """
    raw: Dict[str, dict] = {
        job: record.to_dict()
        for job, record in monitor._records.items()  # noqa: SLF001
    }
    _save_raw(path, raw)


def load_monitor(path: Path) -> HeartbeatMonitor:
    """Restore a :class:`HeartbeatMonitor` from *path*.

    If the file does not exist or cannot be parsed the returned monitor
    starts with an empty record set — equivalent to a freshly constructed
    instance.

    Args:
        path: File previously written by :func:`save_monitor`.

    Returns:
        A :class:`HeartbeatMonitor` populated with the persisted records.
    """
    monitor = HeartbeatMonitor()
    raw = _load_raw(path)
    for job, data in raw.items():
        try:
            monitor._records[job] = HeartbeatRecord.from_dict(data)  # noqa: SLF001
        except (KeyError, ValueError, TypeError):
            # Skip malformed entries rather than crashing on startup.
            continue
    return monitor
