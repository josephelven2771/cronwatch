"""Unit tests for cronwatch.anomaly."""
from __future__ import annotations

import pytest

from cronwatch.anomaly import AnomalyResult, detect_duration_anomaly
from cronwatch.baseline import BaselineStats


def _stats(run_count: int, avg: float, stddev: float) -> BaselineStats:
    return BaselineStats(
        job_name="backup",
        run_count=run_count,
        avg_duration=avg,
        stddev_duration=stddev,
        failure_rate=0.0,
    )


def test_no_stats_returns_no_anomaly():
    result = detect_duration_anomaly("backup", 120.0, stats=None)
    assert result.is_anomaly is False
    assert result.z_score is None


def test_single_run_returns_no_anomaly():
    stats = _stats(run_count=1, avg=120.0, stddev=0.0)
    result = detect_duration_anomaly("backup", 120.0, stats)
    assert result.is_anomaly is False


def test_normal_run_not_anomalous():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    result = detect_duration_anomaly("backup", 105.0, stats)
    assert result.is_anomaly is False
    assert result.z_score == pytest.approx(0.5)


def test_high_z_score_is_anomaly():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    result = detect_duration_anomaly("backup", 135.0, stats)  # z=3.5
    assert result.is_anomaly is True
    assert result.z_score == pytest.approx(3.5)
    assert "longer" in result.reason


def test_low_z_score_is_anomaly():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    result = detect_duration_anomaly("backup", 65.0, stats)  # z=-3.5
    assert result.is_anomaly is True
    assert result.z_score == pytest.approx(-3.5)
    assert "shorter" in result.reason


def test_custom_threshold_respected():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    # z=2.5 — below default 3.0 but above custom 2.0
    result = detect_duration_anomaly("backup", 125.0, stats, z_threshold=2.0)
    assert result.is_anomaly is True


def test_bool_false_when_not_anomaly():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    result = detect_duration_anomaly("backup", 100.0, stats)
    assert not result


def test_bool_true_when_anomaly():
    stats = _stats(run_count=10, avg=100.0, stddev=10.0)
    result = detect_duration_anomaly("backup", 140.0, stats)
    assert result


def test_expected_duration_set_from_stats():
    stats = _stats(run_count=5, avg=60.0, stddev=5.0)
    result = detect_duration_anomaly("backup", 60.0, stats)
    assert result.expected_duration == pytest.approx(60.0)
    assert result.actual_duration == pytest.approx(60.0)


def test_zero_stddev_returns_no_anomaly():
    """When all past runs had identical durations stddev=0; skip z-score."""
    stats = _stats(run_count=5, avg=60.0, stddev=0.0)
    result = detect_duration_anomaly("backup", 9999.0, stats)
    assert result.is_anomaly is False
    assert result.z_score is None
