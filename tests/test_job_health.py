"""Tests for cronwatch.job_health and cronwatch.job_health_checker."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.job_health import (
    HealthSignal,
    JobHealthResult,
    evaluate_job_health,
)
from cronwatch.job_health_checker import JobHealthChecker


# ---------------------------------------------------------------------------
# HealthSignal
# ---------------------------------------------------------------------------

def test_health_signal_ok():
    s = HealthSignal(name="anomaly", ok=True)
    assert s.ok is True


def test_health_signal_not_ok():
    s = HealthSignal(name="threshold", ok=False, detail="failure_rate 0.5 > 0.3")
    assert not s.ok
    assert "failure_rate" in s.detail


# ---------------------------------------------------------------------------
# JobHealthResult
# ---------------------------------------------------------------------------

def test_job_health_result_healthy_when_all_signals_ok():
    result = JobHealthResult(
        job_name="backup",
        signals=[HealthSignal("anomaly", True), HealthSignal("threshold", True)],
    )
    assert result.healthy is True


def test_job_health_result_unhealthy_when_any_signal_fails():
    result = JobHealthResult(
        job_name="backup",
        signals=[HealthSignal("anomaly", True), HealthSignal("threshold", False)],
    )
    assert result.healthy is False


def test_failing_signals_filtered_correctly():
    result = JobHealthResult(
        job_name="sync",
        signals=[
            HealthSignal("anomaly", False, "z=3.5"),
            HealthSignal("trend", True),
            HealthSignal("threshold", False, "too many failures"),
        ],
    )
    failing = result.failing_signals
    assert len(failing) == 2
    assert {s.name for s in failing} == {"anomaly", "threshold"}


def test_summary_healthy():
    result = JobHealthResult(job_name="nightly", signals=[HealthSignal("anomaly", True)])
    assert "healthy" in result.summary()


def test_summary_unhealthy_lists_signals():
    result = JobHealthResult(
        job_name="nightly",
        signals=[HealthSignal("anomaly", False), HealthSignal("trend", False)],
    )
    s = result.summary()
    assert "unhealthy" in s
    assert "anomaly" in s
    assert "trend" in s


def test_to_dict_structure():
    result = JobHealthResult(
        job_name="job1",
        signals=[HealthSignal("window", False, "missed window")],
    )
    d = result.to_dict()
    assert d["job_name"] == "job1"
    assert d["healthy"] is False
    assert d["signals"][0]["name"] == "window"


# ---------------------------------------------------------------------------
# evaluate_job_health
# ---------------------------------------------------------------------------

def _mock_signal(triggered: bool, detail: str = "") -> MagicMock:
    m = MagicMock()
    m.__bool__ = MagicMock(return_value=triggered)
    m.detail = detail
    return m


def test_evaluate_no_signals_is_healthy():
    result = evaluate_job_health("empty_job")
    assert result.healthy is True
    assert result.signals == []


def test_evaluate_anomaly_triggered():
    anomaly = _mock_signal(True, "z=4.1")
    result = evaluate_job_health("job", anomaly=anomaly)
    assert not result.healthy
    assert result.signals[0].name == "anomaly"
    assert result.signals[0].detail == "z=4.1"


def test_evaluate_threshold_not_triggered():
    threshold = _mock_signal(False)
    result = evaluate_job_health("job", threshold=threshold)
    assert result.healthy is True


def test_evaluate_window_ok_is_healthy():
    window = _mock_signal(True)  # window ok == bool(window) is True
    result = evaluate_job_health("job", window=window)
    # window ok means bool(window)=True => HealthSignal ok=True
    assert result.healthy is True


def test_evaluate_window_violated_is_unhealthy():
    window = _mock_signal(False, "missed run window")
    result = evaluate_job_health("job", window=window)
    assert not result.healthy


# ---------------------------------------------------------------------------
# JobHealthChecker
# ---------------------------------------------------------------------------

def _make_checker(job_names, anomalies=None, thresholds=None, trends=None):
    config = MagicMock()
    config.jobs = [MagicMock(name=n) for n in job_names]
    for j, n in zip(config.jobs, job_names):
        j.name = n

    anomaly_checker = MagicMock() if anomalies is not None else None
    threshold_checker = MagicMock() if thresholds is not None else None
    trend_checker = MagicMock() if trends is not None else None

    if anomaly_checker:
        anomaly_checker.check_all.return_value = anomalies
    if threshold_checker:
        threshold_checker.check_all.return_value = thresholds
    if trend_checker:
        trend_checker.check_all.return_value = trends

    return JobHealthChecker(
        config,
        MagicMock(),
        anomaly_checker=anomaly_checker,
        threshold_checker=threshold_checker,
        trend_checker=trend_checker,
    )


def test_check_all_returns_result_for_each_job():
    checker = _make_checker(["job_a", "job_b"])
    results = checker.check_all()
    assert set(results.keys()) == {"job_a", "job_b"}


def test_unhealthy_filters_correctly():
    bad = _mock_signal(True, "high z")
    checker = _make_checker(["ok_job", "bad_job"], anomalies={"bad_job": bad})
    unhealthy = checker.unhealthy()
    names = [r.job_name for r in unhealthy]
    assert "bad_job" in names
    assert "ok_job" not in names


def test_check_all_no_checkers_all_healthy():
    checker = _make_checker(["solo"])
    results = checker.check_all()
    assert results["solo"].healthy is True
