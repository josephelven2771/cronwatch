"""Persistent job run history using a simple JSON file store."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path(os.environ.get("CRONWATCH_HISTORY", "~/.cronwatch_history.json")).expanduser()


def _load_raw(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_raw(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, default=str)


class HistoryEntry:
    def __init__(self, job_name: str, started_at: str, finished_at: Optional[str], exit_code: Optional[int]):
        self.job_name = job_name
        self.started_at = started_at
        self.finished_at = finished_at
        self.exit_code = exit_code

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            job_name=data["job_name"],
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            exit_code=data.get("exit_code"),
        )

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class JobHistory:
    def __init__(self, path: Path = DEFAULT_HISTORY_PATH):
        self.path = path

    def record(self, entry: HistoryEntry) -> None:
        data = _load_raw(self.path)
        data.setdefault(entry.job_name, []).append(entry.to_dict())
        _save_raw(data, self.path)

    def get(self, job_name: str, limit: int = 20) -> List[HistoryEntry]:
        data = _load_raw(self.path)
        entries = data.get(job_name, [])
        return [HistoryEntry.from_dict(e) for e in entries[-limit:]]

    def last(self, job_name: str) -> Optional[HistoryEntry]:
        entries = self.get(job_name, limit=1)
        return entries[-1] if entries else None

    def clear(self, job_name: Optional[str] = None) -> None:
        if job_name is None:
            _save_raw({}, self.path)
        else:
            data = _load_raw(self.path)
            data.pop(job_name, None)
            _save_raw(data, self.path)
