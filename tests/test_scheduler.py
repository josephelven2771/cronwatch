"""Tests for cronwatch.scheduler."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from cronwatch.scheduler import next_run, prev_run, is_overdue, describe_schedule

# Fixed reference point: 2024-06-01 12:00:00 UTC (a Saturday)
NOW = datetime(2024, 6, 1, 12, 0, 0)


def test_next_run_returns_future_datetime():
    nxt = next_run("*/5 * * * *", after=NOW)
    assert nxt > NOW


def test_next_run_five_minute_interval():
    nxt = next_run("*/5 * * * *", after=NOW)
    assert nxt == datetime(2024, 6, 1, 12, 5, 0)


def test_prev_run_returns_past_datetime():
    prv = prev_run("*/5 * * * *", before=NOW)
    assert prv < NOW


def test_prev_run_five_minute_interval():
    prv = prev_run("*/5 * * * *", before=NOW)
    assert prv == datetime(2024, 6, 1, 11, 55, 0)


def test_is_overdue_no_last_seen():
    # Travel 2 minutes past the expected run so grace period is exceeded.
    check_time = datetime(2024, 6, 1, 11, 57, 0)  # 2 min after 11:55 tick
    with patch("cronwatch.scheduler.datetime") as mock_dt:
        mock_dt.utcnow.return_value = check_time
        # prev_run / next_run still need real datetime
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = is_overdue("*/5 * * * *", last_seen=None, grace_seconds=60)
    assert result is True


def test_is_overdue_within_grace_period():
    # Only 30 s past expected; grace=60 → not overdue yet.
    check_time = datetime(2024, 6, 1, 11, 55, 30)
    with patch("cronwatch.scheduler.datetime") as mock_dt:
        mock_dt.utcnow.return_value = check_time
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = is_overdue("*/5 * * * *", last_seen=None, grace_seconds=60)
    assert result is False


def test_is_overdue_last_seen_after_expected():
    expected = datetime(2024, 6, 1, 11, 55, 0)
    last_seen = expected + timedelta(seconds=10)  # ran after expected tick
    check_time = expected + timedelta(seconds=90)  # well past grace
    with patch("cronwatch.scheduler.datetime") as mock_dt:
        mock_dt.utcnow.return_value = check_time
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result = is_overdue("*/5 * * * *", last_seen=last_seen, grace_seconds=60)
    assert result is False


def test_describe_schedule_contains_expression():
    desc = describe_schedule("0 * * * *")
    assert "0 * * * *" in desc
    assert "prev=" in desc
    assert "next=" in desc
