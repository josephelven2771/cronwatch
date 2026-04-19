"""Tests for cronwatch.retrier."""
from unittest.mock import patch
import pytest

from cronwatch.retrier import RetryPolicy, RetryResult, retry


@pytest.fixture
def policy():
    return RetryPolicy(max_attempts=3, delay_seconds=0.0, backoff_factor=2.0)


def _always_succeed():
    return True, "ok"


def _always_fail():
    return False, "error"


def test_retry_succeeds_on_first_attempt(policy):
    result = retry(_always_succeed, policy)
    assert result.succeeded is True
    assert result.attempts == 1


def test_retry_returns_retry_result(policy):
    result = retry(_always_succeed, policy)
    assert isinstance(result, RetryResult)


def test_retry_fails_after_max_attempts(policy):
    result = retry(_always_fail, policy)
    assert result.succeeded is False
    assert result.attempts == 3


def test_retry_records_last_error(policy):
    result = retry(_always_fail, policy)
    assert result.last_error == "error"


def test_retry_collects_all_outputs(policy):
    result = retry(_always_fail, policy)
    assert len(result.outputs) == 3


def test_retry_succeeds_on_third_attempt(policy):
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            return False, "not yet"
        return True, "done"

    result = retry(flaky, policy)
    assert result.succeeded is True
    assert result.attempts == 3


def test_retry_sleeps_between_attempts():
    pol = RetryPolicy(max_attempts=2, delay_seconds=5.0, backoff_factor=1.0)
    with patch("cronwatch.retrier.time.sleep") as mock_sleep:
        retry(_always_fail, pol)
        mock_sleep.assert_called_once_with(5.0)


def test_retry_respects_max_delay():
    pol = RetryPolicy(max_attempts=3, delay_seconds=100.0, backoff_factor=2.0, max_delay_seconds=10.0)
    with patch("cronwatch.retrier.time.sleep") as mock_sleep:
        retry(_always_fail, pol)
        for call in mock_sleep.call_args_list:
            assert call.args[0] <= 10.0
