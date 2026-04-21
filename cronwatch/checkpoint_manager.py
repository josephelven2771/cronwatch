"""CheckpointManager: high-level interface for updating and querying checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from cronwatch.checkpoint import CheckpointStore, JobCheckpoint
from cronwatch.history import HistoryStore


class CheckpointManager:
    """Synchronises checkpoints with the latest history entries."""

    def __init__(self, store: CheckpointStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def record_success(self, job_name: str) -> JobCheckpoint:
        cp = self._store.get_or_create(job_name)
        cp.record_success()
        self._store.save()
        return cp

    def record_failure(self, job_name: str) -> JobCheckpoint:
        cp = self._store.get_or_create(job_name)
        cp.record_failure()
        self._store.save()
        return cp

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get(self, job_name: str) -> Optional[JobCheckpoint]:
        return self._store.get(job_name)

    def consecutive_failures(self, job_name: str) -> int:
        cp = self._store.get(job_name)
        return cp.consecutive_failures if cp else 0

    def all_checkpoints(self) -> List[JobCheckpoint]:
        return list(self._store._data.values())

    def jobs_with_consecutive_failures(self, min_failures: int = 1) -> List[JobCheckpoint]:
        return [
            cp
            for cp in self.all_checkpoints()
            if cp.consecutive_failures >= min_failures
        ]

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_path(cls, path: Path) -> "CheckpointManager":
        store = CheckpointStore.load(path)
        return cls(store)
