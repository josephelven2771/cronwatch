"""Tests for cronwatch.alert_classifier."""
import pytest

from cronwatch.alert_classifier import (
    ClassificationResult,
    Severity,
    classify,
)
from cronwatch.history import HistoryEntry
from datetime import datetime, timezone


def _utc(**kw):
    return datetime(2024, 1, 1, tzinfo=timezone.utc).replace(**kw)


@pytest.fixture()
def success_entry():
    return HistoryEntry(
        job_name="nightly",
        started_at=_utc(hour=1),
        finished_at=_utc(hour=2),
        exit_code=0,
        succeeded=True,
    )


@pytest.fixture()
def failure_entry():
    return HistoryEntry(
        job_name="nightly",
        started_at=_utc(hour=1),
        finished_at=_utc(hour=2),
        exit_code=1,
        succeeded=False,
    )


def test_healthy_job_is_low(success_entry):
    result = classify("nightly", success_entry)
    assert result.severity == Severity.LOW
    assert not bool(result)


def test_single_failure_is_medium(failure_entry):
    result = classify("nightly", failure_entry)
    assert result.severity == Severity.MEDIUM


def test_failure_with_many_consecutive_is_critical(failure_entry):
    result = classify("nightly", failure_entry, consecutive_failures=5)
    assert result.severity == Severity.CRITICAL
    assert bool(result)


def test_high_failure_rate_alone_raises_severity(success_entry):
    result = classify("nightly", success_entry, failure_rate=0.8)
    assert result.severity in (Severity.HIGH, Severity.CRITICAL)


def test_moderate_failure_rate_medium(success_entry):
    result = classify("nightly", success_entry, failure_rate=0.5)
    assert result.severity == Severity.MEDIUM


def test_reasons_populated_on_failure(failure_entry):
    result = classify("nightly", failure_entry, consecutive_failures=3, failure_rate=0.6)
    assert any("failed" in r for r in result.reasons)
    assert any("consecutive" in r for r in result.reasons)
    assert any("failure rate" in r for r in result.reasons)


def test_str_contains_severity_and_job(failure_entry):
    result = classify("nightly", failure_entry)
    text = str(result)
    assert "nightly" in text
    assert result.severity.value.upper() in text


def test_bool_false_for_low_and_medium(success_entry):
    low = classify("j", success_entry)
    assert not bool(low)
    med = classify("j", success_entry, failure_rate=0.5)
    assert not bool(med)


def test_bool_true_for_high(failure_entry):
    result = classify("j", failure_entry, consecutive_failures=2, failure_rate=0.45)
    assert result.severity == Severity.HIGH
    assert bool(result)
