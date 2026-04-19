"""Tests for cronwatch.tag_report."""
import pytest
from unittest.mock import MagicMock
from cronwatch.tag_report import build_tag_report, TagSummary


def _entry(job_name, tags, exit_code=0):
    e = MagicMock()
    e.job_name = job_name
    e.tags = tags
    e.exit_code = exit_code
    return e


@pytest.fixture
def entries():
    return [
        _entry("backup", ["daily", "storage"], exit_code=0),
        _entry("report", ["daily", "email"], exit_code=1),
        _entry("cleanup", ["weekly"], exit_code=0),
        _entry("sync", ["daily"], exit_code=0),
    ]


def test_build_tag_report_keys(entries):
    report = build_tag_report(entries)
    assert "daily" in report
    assert "weekly" in report
    assert "storage" in report


def test_daily_total(entries):
    report = build_tag_report(entries)
    assert report["daily"].total == 3


def test_daily_failures(entries):
    report = build_tag_report(entries)
    assert report["daily"].failures == 1


def test_success_rate_all_ok(entries):
    report = build_tag_report(entries)
    assert report["weekly"].success_rate == 1.0


def test_success_rate_with_failures(entries):
    report = build_tag_report(entries)
    rate = report["daily"].success_rate
    assert abs(rate - 2 / 3) < 0.01


def test_job_names_sorted(entries):
    report = build_tag_report(entries)
    assert report["daily"].job_names == sorted(["backup", "report", "sync"])


def test_str_healthy():
    s = TagSummary(tag="weekly", total=5, failures=0)
    assert "✓" in str(s)
    assert "100%" in str(s)


def test_str_failures():
    s = TagSummary(tag="daily", total=4, failures=2)
    assert "✗" in str(s)
    assert "50%" in str(s)
