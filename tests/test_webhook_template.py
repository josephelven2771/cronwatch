"""Tests for cronwatch.webhook_template."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from cronwatch.history import HistoryEntry
from cronwatch.webhook_template import build_payload, build_json_payload


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def success_entry() -> HistoryEntry:
    e = HistoryEntry(job_name="backup")
    e.started_at = _utc(2024, 6, 1, 2, 0, 0)
    e.finished_at = _utc(2024, 6, 1, 2, 0, 45)
    e.exit_code = 0
    e.succeeded = True
    return e


@pytest.fixture()
def failure_entry() -> HistoryEntry:
    e = HistoryEntry(job_name="cleanup")
    e.started_at = _utc(2024, 6, 1, 3, 0, 0)
    e.finished_at = _utc(2024, 6, 1, 3, 0, 10)
    e.exit_code = 1
    e.succeeded = False
    return e


def test_build_payload_returns_valid_json(success_entry):
    payload = build_payload(success_entry)
    data = json.loads(payload)
    assert isinstance(data, dict)


def test_build_payload_success_status(success_entry):
    data = json.loads(build_payload(success_entry))
    assert data["status"] == "success"
    assert data["job"] == "backup"
    assert data["exit_code"] == 0


def test_build_payload_failure_status(failure_entry):
    data = json.loads(build_payload(failure_entry))
    assert data["status"] == "failure"
    assert data["exit_code"] == 1


def test_build_payload_duration(success_entry):
    data = json.loads(build_payload(success_entry))
    assert data["duration_seconds"] == pytest.approx(45.0)


def test_build_payload_message_contains_job_name(success_entry):
    data = json.loads(build_payload(success_entry))
    assert "backup" in data["message"]


def test_build_payload_custom_template(success_entry):
    tpl = '{"name": "${job_name}", "ok": "${status}"}'
    result = build_payload(success_entry, template_str=tpl)
    data = json.loads(result)
    assert data["name"] == "backup"
    assert data["ok"] == "success"


def test_build_json_payload_returns_dict(success_entry):
    result = build_json_payload(success_entry)
    assert isinstance(result, dict)
    assert result["job"] == "backup"


def test_build_payload_no_timestamps():
    e = HistoryEntry(job_name="noop")
    e.succeeded = True
    e.exit_code = None
    payload = build_payload(e)
    data = json.loads(payload)
    assert data["started_at"] == ""
    assert data["finished_at"] == ""
    assert data["duration_seconds"] == 0.0
    assert data["exit_code"] is None
