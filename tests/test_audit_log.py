"""Tests for cronwatch.audit_log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.audit_log import AuditEntry, AuditLog


@pytest.fixture
def log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit" / "audit.log")


def test_append_creates_file(log: AuditLog, tmp_path: Path) -> None:
    log.append("alert_sent", "backup_job", detail="webhook fired")
    assert (tmp_path / "audit" / "audit.log").exists()


def test_append_returns_audit_entry(log: AuditLog) -> None:
    entry = log.append("alert_sent", "backup_job")
    assert isinstance(entry, AuditEntry)
    assert entry.event == "alert_sent"
    assert entry.job_name == "backup_job"


def test_append_writes_valid_json_line(log: AuditLog, tmp_path: Path) -> None:
    log.append("escalation_triggered", "nightly_sync", detail="3 failures")
    raw = (tmp_path / "audit" / "audit.log").read_text().strip()
    data = json.loads(raw)
    assert data["event"] == "escalation_triggered"
    assert data["job_name"] == "nightly_sync"


def test_read_all_returns_all_entries(log: AuditLog) -> None:
    log.append("alert_sent", "job_a")
    log.append("silence_applied", "job_b")
    log.append("alert_sent", "job_c")
    entries = log.read_all()
    assert len(entries) == 3


def test_read_all_empty_when_no_file(log: AuditLog) -> None:
    assert log.read_all() == []


def test_read_for_job_filters_correctly(log: AuditLog) -> None:
    log.append("alert_sent", "job_a")
    log.append("alert_sent", "job_b")
    log.append("escalation_triggered", "job_a")
    results = log.read_for_job("job_a")
    assert len(results) == 2
    assert all(e.job_name == "job_a" for e in results)


def test_read_by_event_filters_correctly(log: AuditLog) -> None:
    log.append("alert_sent", "job_a")
    log.append("silence_applied", "job_a")
    log.append("alert_sent", "job_b")
    results = log.read_by_event("alert_sent")
    assert len(results) == 2
    assert all(e.event == "alert_sent" for e in results)


def test_tags_are_preserved(log: AuditLog) -> None:
    log.append("alert_sent", "tagged_job", tags=["critical", "infra"])
    entries = log.read_all()
    assert entries[0].tags == ["critical", "infra"]


def test_multiple_appends_accumulate(log: AuditLog) -> None:
    for i in range(5):
        log.append("alert_sent", f"job_{i}")
    assert len(log.read_all()) == 5
