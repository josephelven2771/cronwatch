"""Baseline module: capture and compare job performance baselines."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class BaselineStats:
    job_name: str
    sample_count: int = 0
    total_duration: float = 0.0
    failure_count: int = 0

    @property
    def avg_duration(self) -> Optional[float]:
        if self.sample_count == 0:
            return None
        return self.total_duration / self.sample_count

    @property
    def failure_rate(self) -> float:
        if self.sample_count == 0:
            return 0.0
        return self.failure_count / self.sample_count

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "sample_count": self.sample_count,
            "total_duration": self.total_duration,
            "failure_count": self.failure_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineStats":
        return cls(
            job_name=data["job_name"],
            sample_count=data["sample_count"],
            total_duration=data["total_duration"],
            failure_count=data["failure_count"],
        )


@dataclass
class BaselineDeviation:
    job_name: str
    avg_duration: Optional[float]
    current_duration: float
    threshold_multiplier: float

    @property
    def is_anomalous(self) -> bool:
        if self.avg_duration is None or self.avg_duration == 0:
            return False
        return self.current_duration > self.avg_duration * self.threshold_multiplier


class Baseline:
    """Stores and updates per-job duration/failure baselines."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stats: Dict[str, BaselineStats] = {}
        if path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self._path.read_text())
        self._stats = {k: BaselineStats.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._stats.items()}, indent=2))

    def _get_or_create(self, job_name: str) -> BaselineStats:
        if job_name not in self._stats:
            self._stats[job_name] = BaselineStats(job_name=job_name)
        return self._stats[job_name]

    def record(self, job_name: str, duration: float, succeeded: bool) -> None:
        stats = self._get_or_create(job_name)
        stats.sample_count += 1
        stats.total_duration += duration
        if not succeeded:
            stats.failure_count += 1
        self._save()

    def stats_for(self, job_name: str) -> Optional[BaselineStats]:
        return self._stats.get(job_name)

    def check_deviation(
        self, job_name: str, current_duration: float, threshold_multiplier: float = 2.0
    ) -> BaselineDeviation:
        stats = self._stats.get(job_name)
        avg = stats.avg_duration if stats else None
        return BaselineDeviation(
            job_name=job_name,
            avg_duration=avg,
            current_duration=current_duration,
            threshold_multiplier=threshold_multiplier,
        )
