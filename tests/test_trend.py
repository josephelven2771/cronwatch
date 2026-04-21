"""Unit tests for cronwatch.trend."""
import pytest

from cronwatch.baseline import BaselineStats
from cronwatch.trend import TrendResult, _slope, analyze_trend


# ---------------------------------------------------------------------------
# _slope helpers
# ---------------------------------------------------------------------------

def test_slope_returns_none_for_single_value():
    assert _slope([42.0]) is None


def test_slope_returns_none_for_empty():
    assert _slope([]) is None


def test_slope_flat_series():
    result = _slope([10.0, 10.0, 10.0, 10.0])
    assert result == pytest.approx(0.0, abs=1e-6)


def test_slope_increasing_series():
    # values rise by 2 each step -> slope == 2
    result = _slope([0.0, 2.0, 4.0, 6.0])
    assert result == pytest.approx(2.0, rel=1e-3)


def test_slope_decreasing_series():
    result = _slope([6.0, 4.0, 2.0, 0.0])
    assert result == pytest.approx(-2.0, rel=1e-3)


# ---------------------------------------------------------------------------
# analyze_trend
# ---------------------------------------------------------------------------

@pytest.fixture
def baseline_stats():
    return BaselineStats(
        job_name="backup",
        run_count=50,
        total_duration=5000.0,
        failure_count=5,
    )


def test_unknown_direction_when_no_data(baseline_stats):
    result = analyze_trend("backup", [], baseline_stats)
    assert result.direction == "unknown"
    assert result.duration_slope is None


def test_stable_when_flat_durations(baseline_stats):
    durations = [30.0] * 10
    result = analyze_trend("backup", durations, baseline_stats, recent_failure_rate=0.1)
    assert result.direction == "stable"
    assert result.duration_slope == pytest.approx(0.0, abs=1e-6)


def test_degrading_on_steep_slope(baseline_stats):
    # slope ~10 s/run -> above default threshold of 5
    durations = [float(i * 10) for i in range(10)]
    result = analyze_trend("backup", durations, baseline_stats)
    assert result.direction == "degrading"
    assert bool(result) is True


def test_degrading_on_high_failure_rate_delta(baseline_stats):
    # baseline failure rate = 5/50 = 0.10; recent = 0.25 -> delta = 0.15
    durations = [30.0] * 10
    result = analyze_trend("backup", durations, baseline_stats, recent_failure_rate=0.25)
    assert result.direction == "degrading"
    assert result.failure_rate_delta == pytest.approx(0.15, rel=1e-3)


def test_improving_on_decreasing_durations(baseline_stats):
    durations = [float(100 - i * 10) for i in range(10)]
    result = analyze_trend("backup", durations, baseline_stats, recent_failure_rate=0.05)
    assert result.direction == "improving"
    assert bool(result) is False


def test_no_baseline_still_returns_result():
    durations = [30.0] * 5
    result = analyze_trend("nightly", durations, baseline=None)
    assert isinstance(result, TrendResult)
    assert result.failure_rate_delta is None


def test_note_populated_on_degradation(baseline_stats):
    durations = [float(i * 10) for i in range(10)]
    result = analyze_trend("backup", durations, baseline_stats, recent_failure_rate=0.25)
    assert result.note != ""
