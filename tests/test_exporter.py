"""Tests for cronwatch.exporter."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.digest import Digest, DigestEntry
from cronwatch.exporter import Exporter, digest_to_json, digest_to_text, entry_to_text

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def entry() -> DigestEntry:
    return DigestEntry(
        job_name="backup",
        healthy=True,
        last_run=_NOW,
        message="last run succeeded",
    )


@pytest.fixture()
def problem_entry() -> DigestEntry:
    return DigestEntry(
        job_name="sync",
        healthy=False,
        last_run=None,
        message="never ran",
    )


@pytest.fixture()
def digest(entry, problem_entry) -> Digest:
    return Digest(entries=[entry, problem_entry], generated_at=_NOW)


def test_entry_to_text_healthy(entry):
    text = entry_to_text(entry)
    assert "[OK]" in text
    assert "backup" in text
    assert "last run succeeded" in text


def test_entry_to_text_problem(problem_entry):
    text = entry_to_text(problem_entry)
    assert "[PROBLEM]" in text
    assert "never" in text


def test_digest_to_text_contains_summary(digest):
    text = digest_to_text(digest)
    assert "healthy: 1" in text
    assert "problems: 1" in text


def test_digest_to_json_is_valid(digest):
    raw = digest_to_json(digest)
    data = json.loads(raw)
    assert "entries" in data
    assert len(data["entries"]) == 2


def test_exporter_render_text(digest):
    exp = Exporter(fmt="text")
    out = exp.render(digest)
    assert "cronwatch report" in out


def test_exporter_render_json(digest):
    exp = Exporter(fmt="json")
    out = exp.render(digest)
    data = json.loads(out)
    assert data["healthy_count"] == 1


def test_exporter_invalid_format():
    with pytest.raises(ValueError, match="Unknown format"):
        Exporter(fmt="xml")


def test_exporter_write(tmp_path, digest):
    out_file = tmp_path / "report.txt"
    exp = Exporter(fmt="text")
    exp.write(digest, str(out_file))
    content = out_file.read_text()
    assert content.endswith("\n")
    assert "backup" in content


def test_exporter_write_json(tmp_path, digest):
    """Ensure JSON output written to disk is valid and contains expected fields."""
    out_file = tmp_path / "report.json"
    exp = Exporter(fmt="json")
    exp.write(digest, str(out_file))
    content = out_file.read_text()
    data = json.loads(content)
    assert data["healthy_count"] == 1
    assert data["problem_count"] == 1
    assert len(data["entries"]) == 2
