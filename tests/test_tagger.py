"""Tests for cronwatch.tagger."""
import pytest
from unittest.mock import MagicMock
from cronwatch.tagger import tag_entries, build_tag_index, group_by_tag, TagIndex


def _entry(job_name: str, tags):
    e = MagicMock()
    e.job_name = job_name
    e.tags = tags
    return e


@pytest.fixture
def entries():
    return [
        _entry("backup", ["daily", "storage"]),
        _entry("report", ["daily", "email"]),
        _entry("cleanup", ["weekly"]),
        _entry("ping", []),
    ]


def test_tag_entries_returns_matching(entries):
    result = tag_entries(entries, ["daily"])
    names = [e.job_name for e in result]
    assert "backup" in names
    assert "report" in names
    assert "cleanup" not in names


def test_tag_entries_empty_tags_returns_all(entries):
    result = tag_entries(entries, [])
    assert len(result) == len(entries)


def test_tag_entries_no_match(entries):
    result = tag_entries(entries, ["nonexistent"])
    assert result == []


def test_build_tag_index_get(entries):
    idx = build_tag_index(entries)
    daily = idx.get("daily")
    assert len(daily) == 2


def test_build_tag_index_all_tags(entries):
    idx = build_tag_index(entries)
    tags = idx.all_tags()
    assert "daily" in tags
    assert "weekly" in tags
    assert "storage" in tags


def test_build_tag_index_unknown_tag(entries):
    idx = build_tag_index(entries)
    assert idx.get("missing") == []


def test_group_by_tag(entries):
    groups = group_by_tag(entries)
    assert len(groups["daily"]) == 2
    assert len(groups["weekly"]) == 1
    assert "ping" not in groups  # no tags


def test_entry_no_tags_excluded_from_index():
    e = _entry("silent", [])
    idx = build_tag_index([e])
    assert idx.all_tags() == []
