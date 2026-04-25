"""Tests for cronwatch.alert_debouncer."""
import pytest
from cronwatch.alert_debouncer import AlertDebouncer, DebounceResult


@pytest.fixture
def debouncer() -> AlertDebouncer:
    return AlertDebouncer(recovery_threshold=2)


# ---------------------------------------------------------------------------
# DebounceResult helpers
# ---------------------------------------------------------------------------

def test_debounce_result_bool_true():
    r = DebounceResult("job", True, 1, "reason")
    assert bool(r) is True


def test_debounce_result_bool_false():
    r = DebounceResult("job", False, 2, "reason")
    assert bool(r) is False


# ---------------------------------------------------------------------------
# First failure fires
# ---------------------------------------------------------------------------

def test_first_failure_triggers_alert(debouncer):
    result = debouncer.record_failure("backup")
    assert result.should_alert is True
    assert result.job_name == "backup"
    assert result.consecutive_failures == 1


# ---------------------------------------------------------------------------
# Subsequent failures are suppressed until recovery
# ---------------------------------------------------------------------------

def test_second_failure_suppressed(debouncer):
    debouncer.record_failure("backup")
    result = debouncer.record_failure("backup")
    assert result.should_alert is False
    assert result.consecutive_failures == 2


def test_many_failures_all_suppressed_after_first(debouncer):
    debouncer.record_failure("backup")  # fires
    for _ in range(5):
        result = debouncer.record_failure("backup")
        assert result.should_alert is False


# ---------------------------------------------------------------------------
# Recovery re-arms the debouncer
# ---------------------------------------------------------------------------

def test_not_rearmed_after_single_success_when_threshold_is_two(debouncer):
    debouncer.record_failure("backup")  # arms off
    debouncer.record_success("backup")  # only 1 of 2 needed
    assert debouncer.is_armed("backup") is False


def test_rearmed_after_threshold_successes(debouncer):
    debouncer.record_failure("backup")
    debouncer.record_success("backup")
    debouncer.record_success("backup")  # meets threshold
    assert debouncer.is_armed("backup") is True


def test_failure_fires_again_after_recovery(debouncer):
    debouncer.record_failure("backup")  # first alert
    debouncer.record_success("backup")
    debouncer.record_success("backup")  # re-armed
    result = debouncer.record_failure("backup")  # should alert again
    assert result.should_alert is True


# ---------------------------------------------------------------------------
# Success resets consecutive failure counter
# ---------------------------------------------------------------------------

def test_success_resets_failure_count(debouncer):
    debouncer.record_failure("backup")
    debouncer.record_failure("backup")
    debouncer.record_success("backup")
    debouncer.record_success("backup")  # re-armed
    result = debouncer.record_failure("backup")
    assert result.consecutive_failures == 1


# ---------------------------------------------------------------------------
# Independent state per job
# ---------------------------------------------------------------------------

def test_jobs_are_independent(debouncer):
    r1 = debouncer.record_failure("job-a")
    r2 = debouncer.record_failure("job-b")
    assert r1.should_alert is True
    assert r2.should_alert is True

    r3 = debouncer.record_failure("job-a")  # suppressed
    r4 = debouncer.record_failure("job-b")  # suppressed
    assert r3.should_alert is False
    assert r4.should_alert is False


# ---------------------------------------------------------------------------
# reset() clears state
# ---------------------------------------------------------------------------

def test_reset_clears_state(debouncer):
    debouncer.record_failure("backup")  # disarms
    debouncer.reset("backup")
    assert debouncer.is_armed("backup") is True  # fresh state


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_recovery_threshold_raises():
    with pytest.raises(ValueError):
        AlertDebouncer(recovery_threshold=0)
