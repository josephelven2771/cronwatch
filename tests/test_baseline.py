"""Tests for cronwatch.baseline."""
import json
from pathlib import Path

import pytest

from cronwatch.baseline import Baseline, BaselineStats, BaselineDeviation


@pytest.fixture
def baseline(tmp_path: Path) -> Baseline:
    return Baseline(tmp_path / "baseline.json")


def test_stats_for_unknown_job_returns_none(baseline: Baseline) -> None:
    assert baseline.stats_for("nonexistent") is None


def test_record_creates_stats(baseline: Baseline) -> None:
    baseline.record("backup", duration=10.0, succeeded=True)
    stats = baseline.stats_for("backup")
    assert stats is not None
    assert stats.sample_count == 1
    assert stats.total_duration == 10.0
    assert stats.failure_count == 0


def test_record_failure_increments_failure_count(baseline: Baseline) -> None:
    baseline.record("backup", duration=5.0, succeeded=False)
    stats = baseline.stats_for("backup")
    assert stats.failure_count == 1


def test_avg_duration_across_multiple_records(baseline: Baseline) -> None:
    baseline.record("sync", duration=10.0, succeeded=True)
    baseline.record("sync", duration=20.0, succeeded=True)
    stats = baseline.stats_for("sync")
    assert stats.avg_duration == pytest.approx(15.0)


def test_failure_rate(baseline: Baseline) -> None:
    baseline.record("sync", duration=5.0, succeeded=True)
    baseline.record("sync", duration=5.0, succeeded=False)
    stats = baseline.stats_for("sync")
    assert stats.failure_rate == pytest.approx(0.5)


def test_baseline_persists_to_disk(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    b1 = Baseline(path)
    b1.record("job", duration=8.0, succeeded=True)

    b2 = Baseline(path)
    stats = b2.stats_for("job")
    assert stats is not None
    assert stats.sample_count == 1


def test_check_deviation_not_anomalous(baseline: Baseline) -> None:
    baseline.record("job", duration=10.0, succeeded=True)
    deviation = baseline.check_deviation("job", current_duration=12.0, threshold_multiplier=2.0)
    assert not deviation.is_anomalous


def test_check_deviation_is_anomalous(baseline: Baseline) -> None:
    baseline.record("job", duration=10.0, succeeded=True)
    deviation = baseline.check_deviation("job", current_duration=25.0, threshold_multiplier=2.0)
    assert deviation.is_anomalous


def test_check_deviation_no_history_not_anomalous(baseline: Baseline) -> None:
    deviation = baseline.check_deviation("unknown", current_duration=999.0)
    assert not deviation.is_anomalous
    assert deviation.avg_duration is None


def test_baseline_stats_to_dict_round_trip() -> None:
    stats = BaselineStats(job_name="j", sample_count=3, total_duration=30.0, failure_count=1)
    restored = BaselineStats.from_dict(stats.to_dict())
    assert restored.job_name == stats.job_name
    assert restored.sample_count == stats.sample_count
    assert restored.total_duration == stats.total_duration
    assert restored.failure_count == stats.failure_count
