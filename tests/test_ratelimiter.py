"""Tests for cronwatch.ratelimiter."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from cronwatch.ratelimiter import RateLimiter, RateLimitPolicy, RateLimitResult


@pytest.fixture
def policy() -> RateLimitPolicy:
    return RateLimitPolicy(max_alerts=3, window_seconds=60)


@pytest.fixture
def limiter(policy: RateLimitPolicy) -> RateLimiter:
    return RateLimiter(policy)


def test_check_returns_rate_limit_result(limiter):
    result = limiter.check("job_a")
    assert isinstance(result, RateLimitResult)


def test_initially_allowed(limiter):
    assert limiter.check("job_a").allowed is True


def test_remaining_decrements_after_record(limiter):
    limiter.record("job_a")
    result = limiter.check("job_a")
    assert result.remaining == 2


def test_blocked_after_max_alerts(limiter):
    for _ in range(3):
        limiter.record("job_a")
    result = limiter.check("job_a")
    assert result.allowed is False
    assert result.remaining == 0


def test_allow_returns_true_and_records(limiter):
    allowed = limiter.allow("job_b")
    assert allowed is True
    assert limiter.check("job_b").remaining == 2


def test_allow_returns_false_when_exhausted(limiter):
    for _ in range(3):
        limiter.allow("job_b")
    assert limiter.allow("job_b") is False


def test_window_resets_after_expiry(limiter):
    for _ in range(3):
        limiter.record("job_c")
    assert limiter.check("job_c").allowed is False

    future = datetime.utcnow() + timedelta(seconds=61)
    with patch("cronwatch.ratelimiter.datetime") as mock_dt:
        mock_dt.utcnow.return_value = future
        result = limiter.check("job_c")
    assert result.allowed is True


def test_reset_clears_bucket(limiter):
    for _ in range(3):
        limiter.record("job_d")
    limiter.reset("job_d")
    assert limiter.check("job_d").allowed is True


def test_separate_keys_are_independent(limiter):
    for _ in range(3):
        limiter.record("job_x")
    assert limiter.check("job_y").allowed is True


def test_reset_at_is_future(limiter):
    result = limiter.check("job_e")
    assert result.reset_at > datetime.utcnow()


def test_remaining_never_goes_below_zero(limiter):
    """Remaining count should not go negative when records exceed max_alerts."""
    for _ in range(5):
        limiter.record("job_f")
    result = limiter.check("job_f")
    assert result.remaining == 0
