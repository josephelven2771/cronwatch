"""Tests for cronwatch.summarizer."""
import pytest
from unittest.mock import MagicMock

from cronwatch.digest import Digest, DigestEntry
from cronwatch.summarizer import build_summary, SummaryReport


def _make_entry(name: str, healthy: bool, summary_line: str = "") -> DigestEntry:
    e = MagicMock(spec=DigestEntry)
    e.job_name = name
    e.healthy = healthy
    e.summary_line = summary_line
    return e


@pytest.fixture()
def all_healthy_digest():
    d = MagicMock(spec=Digest)
    d.entries = [
        _make_entry("backup", True, "last run 10m ago, exit 0"),
        _make_entry("cleanup", True, "last run 1h ago, exit 0"),
    ]
    d.healthy_count.return_value = 2
    d.problem_count.return_value = 0
    return d


@pytest.fixture()
def mixed_digest():
    d = MagicMock(spec=Digest)
    d.entries = [
        _make_entry("backup", True, "last run 10m ago, exit 0"),
        _make_entry("nightly", False, "overdue by 2h"),
    ]
    d.healthy_count.return_value = 1
    d.problem_count.return_value = 1
    return d


def test_build_summary_returns_summary_report(all_healthy_digest):
    report = build_summary(all_healthy_digest)
    assert isinstance(report, SummaryReport)


def test_build_summary_counts(all_healthy_digest):
    report = build_summary(all_healthy_digest)
    assert report.total == 2
    assert report.healthy == 2
    assert report.problems == 0


def test_build_summary_all_healthy_message(all_healthy_digest):
    report = build_summary(all_healthy_digest)
    assert "All jobs are healthy." in str(report)


def test_build_summary_problem_message(mixed_digest):
    report = build_summary(mixed_digest)
    assert "1 job(s) require attention." in str(report)


def test_build_summary_includes_job_names(mixed_digest):
    report = build_summary(mixed_digest)
    text = str(report)
    assert "backup" in text
    assert "nightly" in text


def test_build_summary_icons(mixed_digest):
    report = build_summary(mixed_digest)
    text = str(report)
    assert "✓" in text
    assert "✗" in text


def test_str_returns_newline_joined_lines(all_healthy_digest):
    report = build_summary(all_healthy_digest)
    assert str(report) == "\n".join(report.lines)
